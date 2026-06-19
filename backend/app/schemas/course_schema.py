from datetime import datetime
from pydantic import BaseModel


class CreateCourseRequest(BaseModel):
    name: str


class CourseResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}
