from fastapi import APIRouter

# from backend.models.game import GenerateTasksData, GenerateTasksRequest
# from backend.services.llm import llm_service, task_registry

# router = APIRouter(prefix="/tasks", tags=["tasks"])


# @router.post("/generate", response_model=GenerateTasksData)
# def generate_tasks(payload: GenerateTasksRequest) -> GenerateTasksData:
#     tasks = llm_service.generate_tasks(
#         topic=payload.topic,
#         difficulty=payload.difficulty,
#         count=payload.count,
#     )
#     task_registry.put_many(tasks)
#     return GenerateTasksData(tasks=tasks)
