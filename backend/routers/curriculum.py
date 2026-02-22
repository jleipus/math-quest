from fastapi import APIRouter

from backend.models.curriculum import CurriculumTopicsResponse
from backend.services.curriculum import curriculum_service

router = APIRouter(prefix="/curriculum", tags=["curriculum"])


@router.get("/topics", response_model=CurriculumTopicsResponse)
def get_curriculum_topics() -> CurriculumTopicsResponse:
    topics = curriculum_service.get_topics()
    return CurriculumTopicsResponse(topics=topics)
