from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentStatus


class DocumentRepository:
    """Handles all database operations for Document entities."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_document(
        self,
        course_id: int,
        filename: str,
        file_path: str,
        page_count: int = 0,
        status: DocumentStatus = DocumentStatus.UPLOADED,
    ) -> Document:
        doc = Document(
            course_id=course_id,
            filename=filename,
            file_path=file_path,
            page_count=page_count,
            status=status,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def get_documents_by_course(self, course_id: int) -> list[Document]:
        return (
            self.db.query(Document)
            .filter(Document.course_id == course_id)
            .order_by(Document.uploaded_at.desc())
            .all()
        )

    def get_document_by_id(self, document_id: int) -> Document | None:
        return self.db.query(Document).filter(Document.id == document_id).first()

    def update_status(self, document: Document, status: DocumentStatus) -> Document:
        document.status = status
        self.db.commit()
        self.db.refresh(document)
        return document

    def update_processed(self, document: Document, page_count: int) -> Document:
        document.status = DocumentStatus.PROCESSED
        document.page_count = page_count
        document.processed_at = datetime.now(timezone.utc)
        document.error_message = None
        self.db.commit()
        self.db.refresh(document)
        return document

    def update_failed(self, document: Document, error_message: str) -> Document:
        document.status = DocumentStatus.FAILED
        document.error_message = error_message
        self.db.commit()
        self.db.refresh(document)
        return document
