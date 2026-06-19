from pydantic import BaseModel


class AskQuestionRequest(BaseModel):
    question: str


class SourceResponse(BaseModel):
    document_id: int
    filename: str
    page_number: int
    chunk_text: str


class AskQuestionResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]
