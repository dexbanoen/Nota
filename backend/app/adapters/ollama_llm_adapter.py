import httpx
from app.core.config import get_settings

settings = get_settings()

SYSTEM_PROMPT = (
    "You are Nota, a precise local study assistant. "
    "Answer the student's question using ONLY the provided course context.\n\n"
    "Rules:\n"
    "- Be thorough: extract ALL relevant facts, definitions, and details from the context that answer the question.\n"
    "- Be precise: quote or closely paraphrase the source material. Do NOT rephrase in a way that changes meaning.\n"
    "- Cite sources: when stating a fact, reference which page it came from (e.g., 'According to page 5...').\n"
    "- DO NOT invent, assume, or infer information that is not explicitly stated in the context.\n"
    "- If the context contains partial information, present what is available and note what is missing.\n"
    "- If the answer is not in the context at all, say 'I could not find this in the provided material.'\n"
    "- Structure your answer clearly with bullet points or numbered lists when presenting multiple facts.\n"
)


class OllamaLLMAdapter:
    """
    Adapter for generating answers via local Ollama /api/chat endpoint.

    Raises RuntimeError if Ollama is unreachable or returns an error.
    """

    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_llm_model

    def generate(self, context: str, question: str) -> str:
        """
        Build the RAG prompt and ask Ollama for an answer.

        Args:
            context: Concatenated retrieved chunk texts.
            question: The student's question.

        Returns:
            The model's answer as a plain string.
        """
        user_message = (
            f"Context:\n{context}\n\n"
            f"Question:\n{question}\n\n"
            "Answer:"
        )

        try:
            response = httpx.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_message},
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.0,
                        "num_ctx": 8192
                    }
                },
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

