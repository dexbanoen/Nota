import json
from collections.abc import Generator

import httpx
from app.core.config import get_settings

settings = get_settings()

SYSTEM_PROMPT = (
    "Answer using ONLY the provided context. "
    "Be direct and concise — no filler, no preamble. "
    "Cite page numbers inline (e.g. p.5). "
    "If not in context, say 'Not found in material.'"
)

# ── Ollama generation options ─────────────────────────────────────────
# num_predict: hard cap on tokens generated to prevent runaway responses.
# temperature 0.0: deterministic output for factual grounding.
OLLAMA_OPTIONS = {
    "temperature": 0.0,
    "num_ctx": 4096,
    "num_predict": 512,
}


class OllamaLLMAdapter:
    """
    Adapter for generating answers via local Ollama /api/chat endpoint.

    Supports both blocking (generate) and streaming (generate_stream) modes.
    Raises RuntimeError if Ollama is unreachable or returns an error.
    """

    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_llm_model

    def _build_payload(self, context: str, question: str, *, stream: bool) -> dict:
        """Build the Ollama /api/chat request payload."""
        user_message = f"{context}\n\nQ: {question}"
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "stream": stream,
            "options": OLLAMA_OPTIONS,
        }

    # ── Non-streaming (legacy, still used for non-stream endpoint) ────

    def generate(self, context: str, question: str) -> str:
        """
        Generate a complete answer in one blocking call.

        Returns:
            The model's answer as a plain string.
        """
        payload = self._build_payload(context, question, stream=False)

        try:
            response = httpx.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=180.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"].strip()
        except httpx.ConnectError as e:
            raise RuntimeError(
                f"Could not connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running."
            ) from e
        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"Ollama LLM request failed: {e.response.status_code} {e.response.text}"
            ) from e

    # ── Streaming ─────────────────────────────────────────────────────

    def generate_stream(self, context: str, question: str) -> Generator[str, None, None]:
        """
        Stream the answer token-by-token from Ollama.

        Yields:
            Individual text tokens as they are generated.
        """
        payload = self._build_payload(context, question, stream=True)

        try:
            with httpx.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=httpx.Timeout(connect=10.0, read=180.0, write=10.0, pool=10.0),
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    # Each streamed JSON object has message.content with the next token
                    token = data.get("message", {}).get("content", "")
                    if token:
                        yield token
                    # Ollama signals completion with "done": true
                    if data.get("done", False):
                        return
        except httpx.ConnectError as e:
            raise RuntimeError(
                f"Could not connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running."
            ) from e
        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"Ollama LLM request failed: {e.response.status_code} {e.response.text}"
            ) from e
