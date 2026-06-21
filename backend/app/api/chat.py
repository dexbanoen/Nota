from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
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


@router.post("/courses/{course_id}/chat/stream")
def ask_question_stream(
    course_id: int,
    payload: AskQuestionRequest,
    db: Session = Depends(get_db),
):
    """
    Ask a question and receive a streaming answer via Server-Sent Events.

    Event types:
      - event: sources  → JSON array of source objects (sent first)
      - event: token    → a single text token from the LLM
      - event: done     → signals the stream is complete
      - event: error    → an error message
    """
    service = RAGService(db)
    return StreamingResponse(
        service.ask_stream(course_id=course_id, question=payload.question),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
