from fastapi import APIRouter

from backend.models.common import ApiEnvelope, success_response
from backend.models.task import GenerateTasksData, GenerateTasksRequest
from backend.services.llm import llm_service, task_registry

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post(
    "/generate",
    response_model=ApiEnvelope[GenerateTasksData],
)
def generate_tasks(payload: GenerateTasksRequest) -> dict:
    tasks = llm_service.generate_tasks(
        topic=payload.topic,
        difficulty=payload.difficulty,
        count=payload.count,
    )
    task_registry.put_many(tasks)
    return success_response(GenerateTasksData(tasks=tasks).model_dump(mode="json"))
