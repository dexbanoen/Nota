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
        if chunks_with_sources:
            # Format with source attribution so the LLM can cite pages
            parts = []
            for i, chunk in enumerate(chunks_with_sources, 1):
                parts.append(
                    f"[Source {i}: {chunk.filename}, Page {chunk.page_number}]\n{chunk.text}"
                )
            context = "\n\n---\n\n".join(parts)
        else:
            context = "\n\n---\n\n".join(chunk_texts)

        return self._adapter.generate(context=context, question=question)

