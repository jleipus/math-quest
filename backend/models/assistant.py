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
    prompt_used: str
