from pydantic import BaseModel


class TopicRecord(BaseModel):
    """Aggregated performance data for one topic within a session."""

    topic: str
    attempts: int = 0  # total answer submissions
    hints: int = 0  # total hint requests
    correct: int = 0  # tasks answered correctly
