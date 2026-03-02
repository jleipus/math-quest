from fastapi import APIRouter, HTTPException

from backend.models.assistant import HelpResponse, HelpRequest
from backend.services.curriculum import curriculum_service
from backend.services.llm import llm_service
from backend.services.task import task_registry
from backend.services.user_model import user_model_service
from backend.services.vision import rasterize_strokes_to_png

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/help", response_model=HelpResponse)
def request_help(payload: HelpRequest) -> HelpResponse:
    task = task_registry.get(str(payload.task_id))
    if task is None:
        raise HTTPException(status_code=404, detail="Unknown task_id")

    context = curriculum_service.retrieve_context(grade=task.grade, topic=task.topic, question=task.question)

    image_png: bytes | None = None
    if payload.student_work:
        image_png = rasterize_strokes_to_png(payload.student_work)

    user_model_service.record_hint(
        session_id=str(payload.session_id),
        topic=task.topic,
        difficulty=task.difficulty,
    )
    user_model = user_model_service.get_or_create(str(payload.session_id))
    profile_context = user_model.get_profile_context()

    result = llm_service.generate_guidance(
        question=task.question,
        context=context,
        image_png=image_png,
        profile_context=profile_context,
    )

    return HelpResponse(
        guiding_question=result.guiding_question,
        context_used=result.context_used,
    )
