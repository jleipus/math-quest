from fastapi import APIRouter, Depends, HTTPException

from backend.models.user_model import UserModelResponse
from backend.security import verify_firebase_token
from backend.services.firestore_user_model import firestore_user_model_service

router = APIRouter(prefix="/user_model", tags=["user_model"])


@router.get(
    "",
    response_model=UserModelResponse,
)
def get_user_model(
    uid: str | None = Depends(verify_firebase_token),
) -> UserModelResponse:
    if not uid:
        raise HTTPException(status_code=401, detail="Sign in to view your profile.")
    model = firestore_user_model_service.get_or_create(uid)
    return UserModelResponse(topics=model.records)
