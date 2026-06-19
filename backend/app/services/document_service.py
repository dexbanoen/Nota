from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.repositories.document_repository import DocumentRepository
from app.repositories.course_repository import CourseRepository
from app.models.document import Document


class DocumentService:
    """Business logic for document queries (non-ingestion)."""

    def __init__(self, db: Session) -> None:
        self.doc_repo = DocumentRepository(db)
        self.course_repo = CourseRepository(db)

    def get_documents(self, course_id: int) -> list[Document]:
        course = self.course_repo.get_course_by_id(course_id)
        if course is None:
            raise HTTPException(status_code=404, detail=f"Course {course_id} not found.")
        return self.doc_repo.get_documents_by_course(course_id)

    def get_document(self, document_id: int) -> Document:
        doc = self.doc_repo.get_document_by_id(document_id)
        if doc is None:
            raise HTTPException(status_code=404, detail=f"Document {document_id} not found.")
        return doc
