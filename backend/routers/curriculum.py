from fastapi import APIRouter

from backend.models.common import success_response
from backend.models.task import CurriculumTopicsData
from backend.services.curriculum import curriculum_service

router = APIRouter(prefix="/curriculum", tags=["curriculum"])


@router.get("/topics")
def get_curriculum_topics() -> dict:
    topics = curriculum_service.get_topics()
    return success_response(CurriculumTopicsData(topics=topics).model_dump(mode="json"))
