from collections.abc import Generator
from dataclasses import dataclass
from app.adapters.ollama_llm_adapter import OllamaLLMAdapter


@dataclass
class ChunkWithSource:
    """A chunk of text with its source metadata for LLM context."""
    text: str
    filename: str
    page_number: int


class LLMService:
    """
    Service layer wrapping the LLM adapter.

    Builds the context string from chunk texts and delegates to the adapter.
    """

    def __init__(self) -> None:
        self._adapter = OllamaLLMAdapter()

    @staticmethod
    def _build_context(
        chunk_texts: list[str],
        chunks_with_sources: list[ChunkWithSource] | None = None,
    ) -> str:
        """Format chunk texts into a compact context string for the LLM."""
        if chunks_with_sources:
            parts = []
            for chunk in chunks_with_sources:
                parts.append(f"[p.{chunk.page_number}] {chunk.text}")
            return "\n\n".join(parts)
        return "\n\n".join(chunk_texts)

    def generate_answer(self, chunk_texts: list[str], question: str, chunks_with_sources: list[ChunkWithSource] | None = None) -> str:
        """
        Generate a grounded answer from the retrieved chunk texts.

        Args:
            chunk_texts: List of relevant chunk texts retrieved from ChromaDB.
            question: The student's original question.
            chunks_with_sources: Optional list of chunks with source metadata
                for richer context formatting. If provided, chunk_texts is ignored.

        Returns:
            The model's answer as a plain string.
        """
        context = self._build_context(chunk_texts, chunks_with_sources)
        return self._adapter.generate(context=context, question=question)

    def generate_answer_stream(
        self,
        chunk_texts: list[str],
        question: str,
        chunks_with_sources: list[ChunkWithSource] | None = None,
    ) -> Generator[str, None, None]:
        """
        Stream a grounded answer token-by-token.

        Yields:
            Individual text tokens as they are generated.
        """
        context = self._build_context(chunk_texts, chunks_with_sources)
        yield from self._adapter.generate_stream(context=context, question=question)
