from app.adapters.ollama_embedding_adapter import OllamaEmbeddingAdapter


class EmbeddingService:
    """
    Service layer wrapping the embedding adapter.

    The rest of the application calls this; it never calls Ollama directly.
    """

    def __init__(self) -> None:
        self._adapter = OllamaEmbeddingAdapter()

    def embed_text(self, text: str) -> list[float]:
        """Embed a single text and return its vector."""
        return self._adapter.embed(text)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts in a single Ollama request."""
        return self._adapter.embed_batch(texts)
