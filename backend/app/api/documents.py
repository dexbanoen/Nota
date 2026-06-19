from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.document_service import DocumentService
from app.services.ingestion_service import IngestionService
from app.schemas.document_schema import DocumentResponse

router = APIRouter(tags=["documents"])


@router.post(
    "/courses/{course_id}/documents",
    response_model=DocumentResponse,
    status_code=202,
)
def upload_document(
    course_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a PDF file to a course and trigger synchronous ingestion.

    Returns the document record (status may be PROCESSED or FAILED).
    """
    # Basic content-type guard — real validation happens in IngestionService
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=422,
            detail="Only PDF files are supported. Please upload a file with a .pdf extension.",
        )

    file_bytes = file.file.read()

    service = IngestionService(db)
    try:
        document_id = service.ingest(
            course_id=course_id,
            filename=file.filename,
            file_bytes=file_bytes,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    doc_service = DocumentService(db)
    return doc_service.get_document(document_id)


@router.get(
    "/courses/{course_id}/documents",
    response_model=list[DocumentResponse],
)
def list_documents(course_id: int, db: Session = Depends(get_db)):
    service = DocumentService(db)
    return service.get_documents(course_id)


@router.get("/documents/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    service = DocumentService(db)
    return service.get_document(document_id)
