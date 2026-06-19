from datetime import datetime
from pydantic import BaseModel
from app.models.document import DocumentStatus


class DocumentResponse(BaseModel):
    id: int
    course_id: int
    filename: str
    status: DocumentStatus
    page_count: int
    uploaded_at: datetime
    processed_at: datetime | None
    error_message: str | None

    model_config = {"from_attributes": True}
