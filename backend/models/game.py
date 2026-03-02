from uuid import UUID
from typing import Literal

from pydantic import BaseModel, Field


class InitGameRequest(BaseModel):
    grade: str = Field(min_length=1)


class InitGameResponse(BaseModel):
    session_id: UUID
    player_hp: int
    enemy_hp: int
    max_energy: int
    floor: int


class DrawHandRequest(BaseModel):
    session_id: UUID


class Task(BaseModel):
    """Internal task model."""

    task_id: UUID
    question: str
    grade: str
    topic: str
    difficulty: str
    expected_answer: str


class PublicTask(BaseModel):
    """Public task model, excluding expected_answer."""

    task_id: UUID
    question: str
    grade: str
    topic: str
    difficulty: str


CardType = Literal["attack", "heal", "shield"]


class Card(BaseModel):
    card_id: UUID
    card_name: str
    card_power: int
    card_type: CardType
    energy_cost: int
    task: PublicTask


class DrawHandResponse(BaseModel):
    hand: list[Card]
    enemy_next_damage: int


class AnswerRequest(BaseModel):
    session_id: UUID
    task_id: UUID
    answer: str = Field(min_length=1)


class AnswerResponse(BaseModel):
    correct: bool
    card_id: UUID


class PlayCardRequest(BaseModel):
    session_id: UUID
    card_id: UUID


class PlayCardResponse(BaseModel):
    enemy_hp: int
    player_hp: int
    effect_value: int
    card_type: CardType
    enemy_defeated: bool


class EndTurnRequest(BaseModel):
    session_id: UUID


class EndTurnResponse(BaseModel):
    player_hp: int
    enemy_damage: int
    shield_absorbed: int
    hand: list[Card]
    enemy_next_damage: int
    enemy_hp: int
    enemy_max_hp: int
