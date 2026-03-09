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
from backend.security import limiter, verify_firebase_token
from backend.services.curriculum import curriculum_service
from backend.services.firestore_user_model import firestore_user_model_service
from backend.services.game import generate_hand
from backend.services.llm import llm_service
from backend.services.vision import rasterize_strokes_to_png

router = APIRouter(prefix="/game", tags=["game"])


@router.post(
    "/start",
    response_model=StartSessionResponse,
)
def start_session(
    payload: StartSessionRequest,
    uid: str | None = Depends(verify_firebase_token),
) -> StartSessionResponse:
    settings = get_settings()
    return StartSessionResponse(max_energy=settings.max_energy)


@router.post(
    "/hand",
    response_model=FetchHandResponse,
)
@limiter.limit("10/minute")
def fetch_hand(
    request: Request,
    payload: FetchHandRequest,
    uid: str | None = Depends(verify_firebase_token),
) -> FetchHandResponse:
    try:
        hand = generate_hand(
            grade=payload.grade,
            uid=uid,
            client_user_model=payload.user_model,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return FetchHandResponse(hand=hand)


@router.post(
    "/answer",
    response_model=RecordAnswerResponse,
)
def record_answer(
    payload: RecordAnswerRequest,
    uid: str | None = Depends(verify_firebase_token),
) -> RecordAnswerResponse:
    if uid:
        firestore_user_model_service.record_attempt(
            uid=uid,
            topic=payload.topic,
            correct=payload.correct,
            difficulty=payload.difficulty,
        )
    return RecordAnswerResponse(ok=True)


@router.post(
    "/hint",
    response_model=HintResponse,
)
@limiter.limit("20/minute")
def request_hint(
    request: Request,
    payload: HintRequest,
    uid: str | None = Depends(verify_firebase_token),
) -> HintResponse:
    context = curriculum_service.retrieve_context(
        grade=payload.grade,
        topic=payload.topic,
        question=payload.question,
    )

    image_png: bytes | None = None
    if payload.student_work:
        image_png = rasterize_strokes_to_png(payload.student_work, payload.canvas_width, payload.canvas_height)

    if uid:
        profile_context = firestore_user_model_service.get_or_create(uid).get_profile_context()
        firestore_user_model_service.record_hint(
            uid=uid,
            topic=payload.topic,
            difficulty=payload.difficulty,
        )
    else:
        from backend.services.user_model import user_model_to_profile_context

        profile_context = user_model_to_profile_context(payload.user_model) if payload.user_model else ""

    return llm_service.generate_guidance(
        question=payload.question,
        context=context,
        image_png=image_png,
        profile_context=profile_context,
        previous_questions=payload.previous_questions or None,
        session_id=uid or "anonymous",
    )
