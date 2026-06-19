from app.adapters.ollama_llm_adapter import OllamaLLMAdapter


class LLMService:
    """
    Service layer wrapping the LLM adapter.

    Builds the context string from chunk texts and delegates to the adapter.
    """

    def __init__(self) -> None:
        self._adapter = OllamaLLMAdapter()

    def generate_answer(self, chunk_texts: list[str], question: str) -> str:
        """
        Generate a grounded answer from the retrieved chunk texts.

        Args:
            chunk_texts: List of relevant chunk texts retrieved from ChromaDB.
            question: The student's original question.

        Returns:
            The model's answer as a plain string.
        """
        context = "\n\n---\n\n".join(chunk_texts)
        return self._adapter.generate(context=context, question=question)
