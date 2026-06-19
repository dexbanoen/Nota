from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Chunk:
    """A single text chunk with source metadata."""
    page_number: int   # 1-indexed PDF page this chunk came from
    chunk_index: int   # 0-indexed position among chunks on the same page
    text: str


class ChunkingStrategy(ABC):
    """Abstract base class for all chunking strategies."""

    @abstractmethod
    def chunk(self, page_number: int, text: str) -> list[Chunk]:
        """
        Split the text from a single page into one or more Chunk objects.

        Args:
            page_number: The 1-indexed page number the text came from.
            text: The raw page text to chunk.

        Returns:
            A list of Chunk objects (may be empty if text is blank).
        """
        ...
