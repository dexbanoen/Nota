from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.rag_service import RAGService
from app.schemas.chat_schema import AskQuestionRequest, AskQuestionResponse

router = APIRouter(tags=["chat"])


@router.post("/courses/{course_id}/chat", response_model=AskQuestionResponse)
def ask_question(
    course_id: int,
    payload: AskQuestionRequest,
    db: Session = Depends(get_db),
):
    """Ask a question and receive a grounded answer with source citations."""
    service = RAGService(db)
    return service.ask(course_id=course_id, question=payload.question)
