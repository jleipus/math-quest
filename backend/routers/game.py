from fastapi import APIRouter, Depends, HTTPException, Request

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
    InitGameResponseWithToken,
    PlayCardResponse,
    PlayCardRequest,
)
from backend.security import (
    limiter,
    verify_api_key,
    create_session_token,
    verify_session_token,
)
from backend.services.game import game_service
from backend.services.user_model import user_model_service

router = APIRouter(prefix="/game", tags=["game"])


@router.post("/init", response_model=InitGameResponseWithToken, dependencies=[Depends(verify_api_key)])
def init_game(payload: InitGameRequest) -> InitGameResponseWithToken:
    data, _ = game_service.init_game(grade=payload.grade)
    token = create_session_token(str(data.session_id))
    return InitGameResponseWithToken(**data.model_dump(), session_token=token)


@router.post("/draw", response_model=DrawHandResponse, dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
def draw_hand(request: Request, payload: DrawHandRequest) -> DrawHandResponse:
    verify_session_token(str(payload.session_id), payload.x_session_token)
    settings = get_settings()
    with game_service.get_session_locked(str(payload.session_id)) as session:
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        try:
            return game_service.draw_hand(session, hand_size=settings.default_hand_size)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc))


@router.post("/answer", response_model=AnswerResponse, dependencies=[Depends(verify_api_key)])
def answer_task(payload: AnswerRequest) -> AnswerResponse:
    verify_session_token(str(payload.session_id), payload.x_session_token)
    with game_service.get_session_locked(str(payload.session_id)) as session:
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
        if not correct:
            session.record_wrong_attempt(str(card.card_id))
        current_power = session.penalised_power(card)

    # Record attempt outside the session lock, UserModelService has its own lock
    user_model_service.record_attempt(
        session_id=str(payload.session_id),
        topic=card.task.topic,
        correct=correct,
        difficulty=card.task.difficulty,
    )

    return AnswerResponse(correct=correct, card_id=card.card_id, card_power=current_power)


@router.post("/play_card", response_model=PlayCardResponse, dependencies=[Depends(verify_api_key)])
def play_card(payload: PlayCardRequest) -> PlayCardResponse:
    verify_session_token(str(payload.session_id), payload.x_session_token)
    with game_service.get_session_locked(str(payload.session_id)) as session:
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")

        card_id = str(payload.card_id)
        card = session.get_card(card_id)
        if card is None:
            raise HTTPException(status_code=404, detail="Card not found in this session")

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


@router.post("/end_turn", response_model=EndTurnResponse, dependencies=[Depends(verify_api_key)])
def end_turn(payload: EndTurnRequest) -> EndTurnResponse:
    verify_session_token(str(payload.session_id), payload.x_session_token)
    settings = get_settings()
    with game_service.get_session_locked(str(payload.session_id)) as session:
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")

        # If enemy hp <= 0, enemy_attack advances the floor and spawns new enemy
        player_hp, raw_damage, absorbed = game_service.enemy_attack(session)

        try:
            draw_resp = game_service.draw_hand(session, hand_size=settings.default_hand_size)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc))

    return EndTurnResponse(
        player_hp=player_hp,
        enemy_damage=raw_damage,
        shield_absorbed=absorbed,
        hand=draw_resp.hand,
        enemy_next_damage=draw_resp.enemy_next_damage,
        enemy_hp=session.enemy_hp,
        enemy_max_hp=session.enemy_max_hp,
    )
