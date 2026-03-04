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
    canvas_width: int = 512
    canvas_height: int = 512
    previous_questions: list[str] = Field(default_factory=list)


class HelpResponse(BaseModel):
    guiding_question: str
    prompt_used: str
