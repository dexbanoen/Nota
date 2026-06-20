import logging
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
# Cosine distance: 0.0 = identical, 2.0 = opposite.  0.75 is a generous
# cutoff that filters true junk while keeping borderline-useful context.
RELEVANCE_THRESHOLD = 0.75

# How many chunks to pull from ChromaDB (wide net for recall)
RETRIEVAL_LIMIT = 8

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

    def ask(self, course_id: int, question: str) -> AskQuestionResponse:
        # 1. Validate course
        course = self.course_repo.get_course_by_id(course_id)
        if course is None:
            raise HTTPException(status_code=404, detail=f"Course {course_id} not found.")

        # 2. Check for processed documents
        documents = self.doc_repo.get_documents_by_course(course_id)
        processed_docs = [d for d in documents if d.status == DocumentStatus.PROCESSED]

        if not processed_docs:
            return AskQuestionResponse(
                answer=(
                    "This course has no processed documents yet. "
                    "Please upload and wait for your PDF files to finish processing."
                ),
                sources=[],
            )

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

        # 6. No chunks survived filtering
        if not results:
            return AskQuestionResponse(answer=NO_MATERIAL_ANSWER, sources=[])

        # 7. Build context with source attribution and generate answer
        chunks_with_sources = [
            ChunkWithSource(
                text=r.chunk_text,
                filename=r.filename,
                page_number=r.page_number,
            )
            for r in results
        ]
        try:
            answer = self.llm_service.generate_answer(
                chunk_texts=[],
                question=question,
                chunks_with_sources=chunks_with_sources,
            )
        except RuntimeError as e:
            raise HTTPException(status_code=503, detail=str(e))

        # 8. Build and return sources with relevance scores
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

        return AskQuestionResponse(answer=answer, sources=sources)

