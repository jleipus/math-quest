from uuid import UUID
from fastapi import APIRouter

from backend.models.user_model import UserModelResponse
from backend.services.user_model import user_model_service

router = APIRouter(prefix="/user_model", tags=["user_model"])


@router.get("/{session_id}", response_model=UserModelResponse)
def get_user_model(session_id: UUID) -> UserModelResponse:
    model = user_model_service.get_or_create(str(session_id))
    return UserModelResponse(session_id=session_id, topics=model.records)
