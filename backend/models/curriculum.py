from pydantic import BaseModel


class Subtopic(BaseModel):
    """A leaf lesson page under a topic."""

    name: str
    url: str


class Topic(BaseModel):
    """A topic grouping subtopics within a grade."""

    name: str
    url: str
    subtopics: list[Subtopic]


class Grade(BaseModel):
    """A school grade (Årskurs 4/5/6) containing topics."""

    name: str
    url: str
    topics: list[Topic]


class GradesResponse(BaseModel):
    grades: list[str]
