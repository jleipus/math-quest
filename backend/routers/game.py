from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Request

from backend.config import get_settings
from backend.models.assistant import HintRequest, HintResponse
from backend.models.game import (
    FetchHandRequest,
    FetchHandResponse,
    RecordAnswerRequest,
    RecordAnswerResponse,
    StartSessionRequest,
    StartSessionResponse,
)
from backend.security import limiter, verify_api_key
from backend.services.curriculum import curriculum_service
from backend.services.game import generate_hand
from backend.services.llm import llm_service
from backend.services.user_model import user_model_service
from backend.services.vision import rasterize_strokes_to_png

router = APIRouter(prefix="/game", tags=["game"])


@router.post(
    "/start",
    response_model=StartSessionResponse,
    dependencies=[Depends(verify_api_key)],
)
def start_session(payload: StartSessionRequest) -> StartSessionResponse:
    settings = get_settings()
    session_id = uuid4()
    return StartSessionResponse(
        session_id=session_id,
        max_energy=settings.max_energy,
    )


@router.post(
    "/hand",
    response_model=FetchHandResponse,
    dependencies=[Depends(verify_api_key)],
)
@limiter.limit("10/minute")
def fetch_hand(request: Request, payload: FetchHandRequest) -> FetchHandResponse:
    try:
        hand = generate_hand(
            grade=payload.grade,
            session_id=str(payload.session_id),
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return FetchHandResponse(hand=hand)


@router.post(
    "/answer",
    response_model=RecordAnswerResponse,
    dependencies=[Depends(verify_api_key)],
)
def record_answer(payload: RecordAnswerRequest) -> RecordAnswerResponse:
    user_model_service.record_attempt(
        session_id=str(payload.session_id),
        topic=payload.topic,
        correct=payload.correct,
        difficulty=payload.difficulty,
    )
    return RecordAnswerResponse(ok=True)


@router.post(
    "/hint",
    response_model=HintResponse,
    dependencies=[Depends(verify_api_key)],
)
@limiter.limit("20/minute")
def request_hint(request: Request, payload: HintRequest) -> HintResponse:
    context = curriculum_service.retrieve_context(
        grade=payload.grade,
        topic=payload.topic,
        question=payload.question,
    )

    image_png: bytes | None = None
    if payload.student_work:
        image_png = rasterize_strokes_to_png(payload.student_work, payload.canvas_width, payload.canvas_height)

    user_model = user_model_service.get_or_create(str(payload.session_id))
    profile_context = user_model.get_profile_context()

    user_model_service.record_hint(
        session_id=str(payload.session_id),
        topic=payload.topic,
        difficulty=payload.difficulty,
    )

    return llm_service.generate_guidance(
        question=payload.question,
        context=context,
        image_png=image_png,
        profile_context=profile_context,
        previous_questions=payload.previous_questions or None,
        session_id=str(payload.session_id),
    )
