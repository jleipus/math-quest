from uuid import UUID
from typing import Literal

from pydantic import BaseModel, Field


class InitGameRequest(BaseModel):
    topic: str = Field(min_length=1)


class InitGameResponse(BaseModel):
    session_id: UUID
    player_hp: int
    enemy_hp: int
    floor: int = 1


class DrawHandRequest(BaseModel):
    session_id: UUID


class Task(BaseModel):
    task_id: UUID
    question: str
    topic: str
    difficulty: str
    expected_answer: str


CardType = Literal["attack", "heal", "shield"]


class Card(BaseModel):
    card_id: UUID
    card_name: str
    card_power: int
    card_type: CardType
    locked: bool
    task: Task


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
    card_unlocked: bool
    player_hp: int
    message: str


class PlayCardRequest(BaseModel):
    session_id: UUID
    card_id: UUID


class PlayCardResponse(BaseModel):
    enemy_hp: int
    player_hp: int
    effect_value: int
    card_type: CardType
    enemy_defeated: bool
    new_hand: list[Card] | None = None


class EndTurnRequest(BaseModel):
    session_id: UUID


class EndTurnResponse(BaseModel):
    player_hp: int
    enemy_damage: int
    shield_absorbed: int
    hand: list[Card]
    enemy_next_damage: int


class NextFloorRequest(BaseModel):
    session_id: UUID


class NextFloorResponse(BaseModel):
    floor: int
    enemy_hp: int
    enemy_max_hp: int
    enemy_next_damage: int
