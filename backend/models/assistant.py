from pydantic import BaseModel, Field


class Point(BaseModel):
    x: float
    y: float


class Stroke(BaseModel):
    points: list[Point] = Field(default_factory=list)
    timestamp_ms: int


class AnalyseRequest(BaseModel):
    task_id: str = Field(min_length=1)
    content: str = Field(min_length=2)


class AnalyseData(BaseModel):
    has_issue: bool
    message: str
    suggestion: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
