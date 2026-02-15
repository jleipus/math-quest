from fastapi import APIRouter

from backend.models.common import success_response, SuccessResponse
from backend.models.task import CurriculumTopicsData
from backend.services.curriculum import curriculum_service

router = APIRouter(prefix="/curriculum", tags=["curriculum"])


@router.get("/topics", response_model=SuccessResponse[CurriculumTopicsData])
def get_curriculum_topics() -> SuccessResponse[CurriculumTopicsData]:
    topics = curriculum_service.get_topics()
    return success_response(CurriculumTopicsData(topics=topics).model_dump(mode="json"))
