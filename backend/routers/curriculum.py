from fastapi import APIRouter, HTTPException

from backend.models.curriculum import GradesResponse
from backend.services.curriculum import curriculum_service

router = APIRouter(prefix="/curriculum", tags=["curriculum"])


@router.get("/grades", response_model=GradesResponse)
def get_grades() -> GradesResponse:
    """Return available grade names."""
    try:
        return GradesResponse(grades=curriculum_service.get_grades())
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
