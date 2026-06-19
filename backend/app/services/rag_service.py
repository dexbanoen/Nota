import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.repositories.course_repository import CourseRepository
from app.repositories.document_repository import DocumentRepository
from app.models.document import DocumentStatus
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.vector_store.chroma_store import ChromaStore, ChunkResult
from app.schemas.chat_schema import AskQuestionResponse, SourceResponse

logger = logging.getLogger(__name__)

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
    4. Retrieve top-5 relevant chunks from ChromaDB (filtered by course_id)
    5. If no chunks, return a helpful message
    6. Build context and generate an LLM answer
    7. Return answer + sources
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

        # 4. Retrieve top-3 relevant chunks
        try:
            results: list[ChunkResult] = self.chroma.search(
                course_id=course_id,
                query_embedding=query_embedding,
                limit=3,
            )
        except Exception as e:
            logger.error("ChromaDB search failed: %s", e)
            raise HTTPException(status_code=503, detail="Vector store search failed.")

        # 5. No chunks found
        if not results:
            return AskQuestionResponse(answer=NO_MATERIAL_ANSWER, sources=[])

        # 6. Build context and generate answer
        chunk_texts = [r.chunk_text for r in results]
        try:
            answer = self.llm_service.generate_answer(chunk_texts, question)
        except RuntimeError as e:
            raise HTTPException(status_code=503, detail=str(e))

        # 7. Build and return sources
        sources = [
            SourceResponse(
                document_id=r.document_id,
                filename=r.filename,
                page_number=r.page_number,
                chunk_text=r.chunk_text,
            )
            for r in results
        ]

        return AskQuestionResponse(answer=answer, sources=sources)
