from uuid import UUID
from pydantic import BaseModel


class DifficultyRecord(BaseModel):
    topic: str
    difficulty: str
    attempts: int = 0  # total answer submissions
    hints: int = 0  # total hint requests
    correct: int = 0  # tasks answered correctly


class TopicRecord(BaseModel):
    """Aggregated performance data for one topic within a session."""

    topic: str
    records: dict[str, DifficultyRecord]


class UserModelResponse(BaseModel):
    session_id: UUID
    topics: list[TopicRecord]
