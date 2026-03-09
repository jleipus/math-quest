from uuid import UUID
from typing import Literal

from pydantic import BaseModel, Field


class Task(BaseModel):
    task_id: UUID
    question: str
    grade: str
    topic: str
    difficulty: str
    expected_answer: str


CardType = Literal["attack", "heal", "shield"]
AttackSubtype = Literal["magic", "bow", "sword", "axe"]


class Card(BaseModel):
    card_id: UUID
    card_name: str
    card_power: int
    card_type: CardType
    attack_subtype: AttackSubtype | None = None
    energy_cost: int
    task: Task


class StartSessionRequest(BaseModel):
    grade: str = Field(min_length=1)


class StartSessionResponse(BaseModel):
    session_id: UUID
    max_energy: int


class FetchHandRequest(BaseModel):
    session_id: UUID
    grade: str = Field(min_length=1)


class FetchHandResponse(BaseModel):
    hand: list[Card]


class RecordAnswerRequest(BaseModel):
    session_id: UUID
    topic: str = Field(min_length=1)
    difficulty: str = Field(min_length=1)
    correct: bool


class RecordAnswerResponse(BaseModel):
    ok: bool = True
