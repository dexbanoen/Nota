from app.chunking.base import Chunk, ChunkingStrategy

DEFAULT_MAX_CHARS = 2500
DEFAULT_OVERLAP = 300


class PageChunkingStrategy(ChunkingStrategy):
    """
    Chunks page text into overlapping windows.

    - If the entire page text fits within max_chars, it becomes a single chunk.
    - Otherwise the text is split into overlapping windows of max_chars characters
      with an overlap of overlap_chars characters between consecutive chunks.
    - Empty pages produce no chunks.
    """

    def __init__(
        self,
        max_chars: int = DEFAULT_MAX_CHARS,
        overlap_chars: int = DEFAULT_OVERLAP,
    ) -> None:
        self.max_chars = max_chars
        self.overlap_chars = overlap_chars

    def chunk(self, page_number: int, text: str) -> list[Chunk]:
        text = text.strip()
        if not text:
            return []

        # If the page fits in a single chunk, return it directly
        if len(text) <= self.max_chars:
            return [Chunk(page_number=page_number, chunk_index=0, text=text)]

        # Sliding window split with overlap, snapping to sentence boundaries
        chunks: list[Chunk] = []
        start = 0
        chunk_index = 0
        step = self.max_chars - self.overlap_chars

        while start < len(text):
            end = min(start + self.max_chars, len(text))

            # Snap to sentence boundary (don't cut mid-sentence)
            if end < len(text):
                end = self._snap_to_sentence(text, start, end)

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    Chunk(
                        page_number=page_number,
                        chunk_index=chunk_index,
                        text=chunk_text,
                    )
                )
                chunk_index += 1
            start = max(start + step, end - self.overlap_chars)

        return chunks

    @staticmethod
    def _snap_to_sentence(text: str, start: int, end: int) -> int:
        """
        Move `end` backward to the nearest sentence boundary so chunks
        don't split mid-sentence. Falls back to the original end if no
        good boundary is found in the back half of the window.
        """
        # Search region: only look in the back 40% of the chunk to avoid
        # trimming too aggressively
        search_start = start + int((end - start) * 0.6)
        region = text[search_start:end]

        # Try sentence-ending punctuation followed by whitespace or newline
        for sep in ['. ', '.\n', '? ', '?\n', '! ', '!\n', '\n\n']:
            pos = region.rfind(sep)
            if pos != -1:
                return search_start + pos + len(sep)

        return end
