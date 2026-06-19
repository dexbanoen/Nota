import httpx
from app.core.config import get_settings

settings = get_settings()


class OllamaEmbeddingAdapter:
    """
    Adapter for generating text embeddings via local Ollama /api/embed endpoint.

    Raises RuntimeError if Ollama is unreachable or returns an error.
    """

    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_embedding_model

    def embed(self, text: str) -> list[float]:
        """Embed a single text string and return its embedding vector."""
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a list of texts in one request.

        Ollama /api/embed accepts an 'input' field as list[str].
        """
        try:
            response = httpx.post(
                f"{self.base_url}/api/embed",
                json={"model": self.model, "input": texts},
                timeout=120.0,
            )
            response.raise_for_status()
            data = response.json()
            embeddings = data.get("embeddings")
            if not embeddings:
                raise RuntimeError("Ollama returned no embeddings in response.")
            return embeddings
        except httpx.ConnectError as e:
            raise RuntimeError(
                f"Could not connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running."
            ) from e
        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"Ollama embedding request failed: {e.response.status_code} {e.response.text}"
            ) from e
