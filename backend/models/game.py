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


class InitGameResponseWithToken(InitGameResponse):
    """Extends InitGameResponse with the one-time session token."""
    session_token: str


class SessionTokenRequest(BaseModel):
    """Mixin — all session-scoped requests carry the session token."""
    session_id: UUID
    x_session_token: str = Field(min_length=1)


class DrawHandRequest(SessionTokenRequest):
    pass


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
AttackSubtype = Literal["magic", "bow", "sword", "axe"]


class Card(BaseModel):
    card_id: UUID
    card_name: str
    card_power: int
    card_type: CardType
    attack_subtype: AttackSubtype | None = None
    energy_cost: int
    task: PublicTask


class DrawHandResponse(BaseModel):
    hand: list[Card]
    enemy_next_damage: int


class AnswerRequest(SessionTokenRequest):
    task_id: UUID
    answer: str = Field(min_length=1)


class AnswerResponse(BaseModel):
    correct: bool
    card_id: UUID


class PlayCardRequest(SessionTokenRequest):
    card_id: UUID


class PlayCardResponse(BaseModel):
    enemy_hp: int
    player_hp: int
    effect_value: int
    card_type: CardType
    enemy_defeated: bool


class EndTurnRequest(SessionTokenRequest):
    pass


class EndTurnResponse(BaseModel):
    player_hp: int
    enemy_damage: int
    shield_absorbed: int
    hand: list[Card]
    enemy_next_damage: int
    enemy_hp: int
    enemy_max_hp: int
