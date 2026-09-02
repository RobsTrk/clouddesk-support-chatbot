from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: str | None = Field(default=None, max_length=100)

class ChatResponse(BaseModel):
    query_id: int
    answer: str
    confidence: float
    escalated: bool
    needs_clarification: bool = False
    sources: list[str]
    conversation_id: str
    intent: str
    intent_confidence: float
    escalation_reason: str | None = None

class FeedbackRequest(BaseModel):
    query_id: int
    helpful: bool
    comment: str | None = Field(default=None, max_length=2000)
