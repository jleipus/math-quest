from uuid import UUID

from pydantic import BaseModel, Field


class GenerateTasksRequest(BaseModel):
    topic: str = Field(min_length=1)
    difficulty: str = Field(pattern="^(easy|medium|hard)$")
    count: int = Field(default=1, ge=1, le=10)


class TaskItem(BaseModel):
    task_id: UUID
    question: str
    expected_answer: str
    topic: str
    difficulty: str


class GenerateTasksData(BaseModel):
    tasks: list[TaskItem]


class CurriculumTopic(BaseModel):
    id: str
    name: str
    subtopics: list[str]
    grade_level: str


class CurriculumTopicsData(BaseModel):
    topics: list[CurriculumTopic]
