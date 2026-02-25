from fastapi import APIRouter, HTTPException

from backend.models.common import ApiEnvelope, success_response
from backend.models.task import CurriculumTopicsData
from backend.services.curriculum import curriculum_service

router = APIRouter(prefix="/curriculum", tags=["curriculum"])


@router.get("/topics", response_model=ApiEnvelope[CurriculumTopicsData])
def get_curriculum_topics() -> dict:
    try:
        topics = curriculum_service.get_topics()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return success_response(CurriculumTopicsData(topics=topics).model_dump(mode="json"))
