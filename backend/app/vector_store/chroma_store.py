from dataclasses import dataclass
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import get_settings

settings = get_settings()


@dataclass
class ChunkResult:
    """Represents a single search result from ChromaDB."""
    document_id: int
    filename: str
    page_number: int
    chunk_text: str
    distance: float | None = None


@dataclass
class ChunkRecord:
    """Input record for storing a chunk in ChromaDB."""
    id: str
    text: str
    embedding: list[float]
    course_id: int
    document_id: int
    filename: str
    page_number: int
    chunk_index: int


class ChromaStore:
    """
    Abstraction over ChromaDB for storing and retrieving chunk embeddings.

    Uses a persistent local client so data survives restarts.
    Chunks are filtered by course_id at query time for course-scoped search.
    """

    def __init__(self) -> None:
        self._client = chromadb.PersistentClient(
            path=settings.chroma_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        # Get or create the collection with cosine similarity
        self._collection = self._client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, chunks: list[ChunkRecord]) -> None:
        """
        Upsert a list of chunk records into ChromaDB.

        Upserting ensures idempotency: re-ingesting the same document
        will overwrite old chunks rather than create duplicates.
        """
        if not chunks:
            return

        self._collection.upsert(
            ids=[c.id for c in chunks],
            documents=[c.text for c in chunks],
            embeddings=[c.embedding for c in chunks],
            metadatas=[
                {
                    "course_id": c.course_id,
                    "document_id": c.document_id,
                    "filename": c.filename,
                    "page_number": c.page_number,
                    "chunk_index": c.chunk_index,
                }
                for c in chunks
            ],
        )

    def search(
        self,
        course_id: int,
        query_embedding: list[float],
        limit: int = 5,
    ) -> list[ChunkResult]:
        """
        Search for the most relevant chunks within a specific course.

        Args:
            course_id: Only return chunks belonging to this course.
            query_embedding: The query's embedding vector.
            limit: Maximum number of results to return.

        Returns:
            List of ChunkResult ordered by relevance (closest first).
        """
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where={"course_id": course_id},
            include=["documents", "metadatas", "distances"],
        )

        chunk_results: list[ChunkResult] = []
        documents = results.get("documents") or [[]]
        metadatas = results.get("metadatas") or [[]]
        distances = results.get("distances") or [[]]

        for doc, meta, dist in zip(documents[0], metadatas[0], distances[0]):
            chunk_results.append(
                ChunkResult(
                    document_id=int(meta["document_id"]),
                    filename=str(meta["filename"]),
                    page_number=int(meta["page_number"]),
                    chunk_text=doc,
                    distance=dist,
                )
            )

        return chunk_results

    def delete_document_chunks(self, document_id: int) -> None:
        """Delete all chunks belonging to a specific document."""
        self._collection.delete(where={"document_id": document_id})
