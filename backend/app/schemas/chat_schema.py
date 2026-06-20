from pydantic import BaseModel


class AskQuestionRequest(BaseModel):
    question: str


class SourceResponse(BaseModel):
    document_id: int
    filename: str
    page_number: int
    chunk_text: str
    relevance_score: float = 0.0  # 0.0–1.0, higher = more relevant


class AskQuestionResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]

