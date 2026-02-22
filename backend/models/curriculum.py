from pydantic import BaseModel


class CurriculumTopic(BaseModel):
    id: str
    name: str
    subtopics: list[str]
    grade_level: str


class CurriculumTopicsResponse(BaseModel):
    topics: list[CurriculumTopic]
