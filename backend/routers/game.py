from fastapi import APIRouter, HTTPException

from backend.config import get_settings
from backend.models.game import (
    AnswerResponse,
    AnswerRequest,
    DrawHandRequest,
    DrawHandResponse,
    EndTurnRequest,
    EndTurnResponse,
    InitGameRequest,
    InitGameResponse,
    NextFloorRequest,
    NextFloorResponse,
    PlayCardResponse,
    PlayCardRequest,
)
from backend.services.game import game_service

router = APIRouter(prefix="/game", tags=["game"])


@router.post("/init", response_model=InitGameResponse)
def init_game(payload: InitGameRequest) -> InitGameResponse:
    """Create a new game session without dealing cards yet."""
    data, _ = game_service.init_game(topic=payload.topic)
    return data


@router.post("/draw", response_model=DrawHandResponse)
def draw_hand(payload: DrawHandRequest) -> DrawHandResponse:
    """Deal a fresh hand of mixed-difficulty cards into an existing session."""
    settings = get_settings()
    session = game_service.get_session(str(payload.session_id))
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return game_service.draw_hand(session, hand_size=settings.default_hand_size)


@router.post("/answer", response_model=AnswerResponse)
def answer_task(payload: AnswerRequest) -> AnswerResponse:
    session = game_service.get_session(str(payload.session_id))
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    task_id = str(payload.task_id)
    card = session.get_card_for_task(task_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Task not found in this session")

    expected = session.get_expected_answer(task_id)
    if expected is None:
        raise HTTPException(status_code=500, detail="Expected answer missing")

    correct = game_service.check_answer(payload.answer, expected)

    if correct:
        session.unlock_card(str(card.card_id))
        return AnswerResponse(
            correct=True,
            card_id=card.card_id,
            card_unlocked=True,
            player_hp=session.player_hp,
            message="Correct! Card unlocked.",
        )

    return AnswerResponse(
        correct=False,
        card_id=card.card_id,
        card_unlocked=False,
        player_hp=session.player_hp,
        message="Not quite — try again!",
    )


@router.post("/play_card", response_model=PlayCardResponse)
def play_card(payload: PlayCardRequest) -> PlayCardResponse:
    session = game_service.get_session(str(payload.session_id))
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    card_id = str(payload.card_id)
    card = session.get_card(card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found in this session")
    if card.locked:
        raise HTTPException(status_code=400, detail="Card is still locked — solve the task first")

    enemy_hp, player_hp = game_service.apply_card(session, card)
    session.remove_card(card_id)

    enemy_defeated = session.enemy_hp <= 0

    return PlayCardResponse(
        enemy_hp=enemy_hp,
        player_hp=player_hp,
        effect_value=card.card_power,
        card_type=card.card_type,
        enemy_defeated=enemy_defeated,
    )


@router.post("/end_turn", response_model=EndTurnResponse)
def end_turn(payload: EndTurnRequest) -> EndTurnResponse:
    settings = get_settings()
    session = game_service.get_session(str(payload.session_id))
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    player_hp, raw_damage, absorbed = game_service.enemy_attack(session)

    draw_resp = game_service.draw_hand(session, hand_size=settings.default_hand_size)

    return EndTurnResponse(
        player_hp=player_hp,
        enemy_damage=raw_damage,
        shield_absorbed=absorbed,
        hand=draw_resp.hand,
        enemy_next_damage=draw_resp.enemy_next_damage,
    )


@router.post("/next_floor", response_model=NextFloorResponse)
def next_floor(payload: NextFloorRequest) -> NextFloorResponse:
    """Advance to the next floor, spawning a stronger enemy."""
    session = game_service.get_session(str(payload.session_id))
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return game_service.next_floor(session)
