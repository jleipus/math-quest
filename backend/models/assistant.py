from pydantic import BaseModel, Field

from backend.models.user_model import TopicRecord


class Point(BaseModel):
    x: float
    y: float


class Stroke(BaseModel):
    points: list[Point] = Field(default_factory=list)
    timestamp_ms: int


class HintRequest(BaseModel):
    # Task context
    grade: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    difficulty: str = Field(min_length=1)
    question: str = Field(min_length=1)

    # Client-supplied user model for anonymous users
    user_model: list[TopicRecord] | None = None

    # Optional student work
    student_work: list[Stroke] | None = None
    canvas_width: int = 512
    canvas_height: int = 512
    previous_questions: list[str] = Field(default_factory=list)


class HintResponse(BaseModel):
    guiding_question: str
