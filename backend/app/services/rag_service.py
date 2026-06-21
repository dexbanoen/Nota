import json
import logging
from collections.abc import Generator

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.repositories.course_repository import CourseRepository
from app.repositories.document_repository import DocumentRepository
from app.models.document import DocumentStatus
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService, ChunkWithSource
from app.vector_store.chroma_store import ChromaStore, ChunkResult
from app.schemas.chat_schema import AskQuestionResponse, SourceResponse

logger = logging.getLogger(__name__)

# Cosine distance threshold — chunks above this are considered irrelevant.
# Cosine distance: 0.0 = identical, 2.0 = opposite.  0.60 is a tighter
# cutoff that keeps high-quality context and filters weak matches.
RELEVANCE_THRESHOLD = 0.60

# How many chunks to pull from ChromaDB.
# Reduced from 8 → 5 to send less context to the LLM, which directly
# reduces generation time while preserving recall for most queries.
RETRIEVAL_LIMIT = 5

NO_MATERIAL_ANSWER = (
    "I could not find this in the uploaded course material. "
    "Please make sure you have uploaded and processed relevant PDF files for this course."
)


class RAGService:
    """
    Retrieval-Augmented Generation service.

    Flow:
    1. Validate course exists
    2. Validate course has processed documents
    3. Embed the question
    4. Retrieve top-N relevant chunks from ChromaDB (filtered by course_id)
    5. Filter by relevance threshold and deduplicate overlapping chunks
    6. If no chunks survive, return a helpful message
    7. Build context and generate an LLM answer
    8. Return answer + sources (with relevance scores)
    """

    def __init__(self, db: Session) -> None:
        self.course_repo = CourseRepository(db)
        self.doc_repo = DocumentRepository(db)
        self.embedding_service = EmbeddingService()
        self.llm_service = LLMService()
        self.chroma = ChromaStore()

    # ──────────────────────────────────────────────────────────────
    # Shared retrieval logic
    # ──────────────────────────────────────────────────────────────

    def _validate_and_retrieve(
        self, course_id: int, question: str
    ) -> tuple[list[ChunkResult], list[ChunkWithSource], list[SourceResponse]] | None:
        """
        Validate course, embed question, retrieve + filter chunks.

        Returns:
            (results, chunks_with_sources, sources) or None if no chunks.
            Raises HTTPException for validation or infrastructure errors.
        """
        # 1. Validate course
        course = self.course_repo.get_course_by_id(course_id)
        if course is None:
            raise HTTPException(status_code=404, detail=f"Course {course_id} not found.")

        # 2. Check for processed documents
        documents = self.doc_repo.get_documents_by_course(course_id)
        processed_docs = [d for d in documents if d.status == DocumentStatus.PROCESSED]

        if not processed_docs:
            return None

        # 3. Embed the question
        try:
            query_embedding = self.embedding_service.embed_text(question)
        except RuntimeError as e:
            raise HTTPException(status_code=503, detail=str(e))

        # 4. Retrieve top-N relevant chunks (wide net)
        try:
            results: list[ChunkResult] = self.chroma.search(
                course_id=course_id,
                query_embedding=query_embedding,
                limit=RETRIEVAL_LIMIT,
            )
        except Exception as e:
            logger.error("ChromaDB search failed: %s", e)
            raise HTTPException(status_code=503, detail="Vector store search failed.")

        # 5. Filter by relevance threshold — remove chunks that are too distant
        results = [
            r for r in results
            if r.distance is not None and r.distance < RELEVANCE_THRESHOLD
        ]

        # Deduplicate: if two chunks come from the same document + same page,
        # keep only the one with the lower distance (more relevant).
        # This prevents overlapping sliding-window chunks from flooding context.
        seen_keys: dict[tuple[int, int], ChunkResult] = {}
        for r in results:
            key = (r.document_id, r.page_number)
            if key not in seen_keys or (r.distance or 2.0) < (seen_keys[key].distance or 2.0):
                seen_keys[key] = r
        results = list(seen_keys.values())

        # Re-sort by distance (best first) after dedup
        results.sort(key=lambda r: r.distance or 2.0)

        logger.info(
            "RAG retrieval: %d chunks survived filtering (threshold=%.2f) for course %d",
            len(results), RELEVANCE_THRESHOLD, course_id,
        )

        if not results:
            return None

        # Build shared data structures
        chunks_with_sources = [
            ChunkWithSource(
                text=r.chunk_text,
                filename=r.filename,
                page_number=r.page_number,
            )
            for r in results
        ]

        sources = [
            SourceResponse(
                document_id=r.document_id,
                filename=r.filename,
                page_number=r.page_number,
                chunk_text=r.chunk_text,
                relevance_score=round(1.0 - (r.distance or 0.0), 3),
            )
            for r in results
        ]

        return results, chunks_with_sources, sources

    # ──────────────────────────────────────────────────────────────
    # Non-streaming (original)
    # ──────────────────────────────────────────────────────────────

    def ask(self, course_id: int, question: str) -> AskQuestionResponse:
        retrieval = self._validate_and_retrieve(course_id, question)

        if retrieval is None:
            # Either no processed docs or no relevant chunks
            documents = self.doc_repo.get_documents_by_course(course_id)
            processed = [d for d in documents if d.status == DocumentStatus.PROCESSED]
            if not processed:
                return AskQuestionResponse(
                    answer=(
                        "This course has no processed documents yet. "
                        "Please upload and wait for your PDF files to finish processing."
                    ),
                    sources=[],
                )
            return AskQuestionResponse(answer=NO_MATERIAL_ANSWER, sources=[])

        _results, chunks_with_sources, sources = retrieval

        try:
            answer = self.llm_service.generate_answer(
                chunk_texts=[],
                question=question,
                chunks_with_sources=chunks_with_sources,
            )
        except RuntimeError as e:
            raise HTTPException(status_code=503, detail=str(e))

        return AskQuestionResponse(answer=answer, sources=sources)

    # ──────────────────────────────────────────────────────────────
    # Streaming (new — yields SSE events)
    # ──────────────────────────────────────────────────────────────

    def ask_stream(self, course_id: int, question: str) -> Generator[str, None, None]:
        """
        Stream the RAG answer as Server-Sent Events (SSE).

        Event types:
          - event: sources   → JSON array of source objects (sent first)
          - event: token     → a single text token from the LLM
          - event: done      → signals the stream is complete
          - event: error     → an error message
        """
        # Validate and retrieve
        try:
            retrieval = self._validate_and_retrieve(course_id, question)
        except HTTPException as exc:
            yield f"event: error\ndata: {json.dumps({'detail': exc.detail})}\n\n"
            return

        if retrieval is None:
            documents = self.doc_repo.get_documents_by_course(course_id)
            processed = [d for d in documents if d.status == DocumentStatus.PROCESSED]
            if not processed:
                msg = (
                    "This course has no processed documents yet. "
                    "Please upload and wait for your PDF files to finish processing."
                )
            else:
                msg = NO_MATERIAL_ANSWER
            # Send the full answer as a single token so the frontend can display it
            yield f"event: sources\ndata: []\n\n"
            yield f"event: token\ndata: {json.dumps(msg)}\n\n"
            yield "event: done\ndata: {}\n\n"
            return

        _results, chunks_with_sources, sources = retrieval

        # 1. Emit sources first so the frontend can display them immediately
        sources_json = json.dumps([s.model_dump() for s in sources])
        yield f"event: sources\ndata: {sources_json}\n\n"

        # 2. Stream LLM tokens
        try:
            for token in self.llm_service.generate_answer_stream(
                chunk_texts=[],
                question=question,
                chunks_with_sources=chunks_with_sources,
            ):
                yield f"event: token\ndata: {json.dumps(token)}\n\n"
        except RuntimeError as e:
            yield f"event: error\ndata: {json.dumps({'detail': str(e)})}\n\n"
            return

        # 3. Signal completion
        yield "event: done\ndata: {}\n\n"
