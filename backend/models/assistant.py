from uuid import UUID

from pydantic import BaseModel, Field


class Point(BaseModel):
    x: float
    y: float


class Stroke(BaseModel):
    points: list[Point] = Field(default_factory=list)
    timestamp_ms: int


class HelpRequest(BaseModel):
    session_id: UUID
    task_id: UUID
    student_work: list[Stroke] | None = None


class HelpResponse(BaseModel):
    guiding_question: str
    context_used: str


class AnalysisRequest(BaseModel):
    task_id: str = Field(min_length=1)
    content: str = Field(min_length=2)


class AnalysisResponse(BaseModel):
    has_issue: bool
    message: str
    suggestion: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
