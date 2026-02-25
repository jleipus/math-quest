import json
from typing import Any

from fastapi import APIRouter, HTTPException

from backend.models.assistant import AnalyseData, AnalyseRequest, Stroke
from backend.models.common import ApiEnvelope, success_response
from backend.services.llm import llm_service, task_registry
from backend.services.vision import rasterize_strokes_to_png

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/analyse", response_model=ApiEnvelope[AnalyseData])
def analyse(payload: AnalyseRequest) -> dict[str, Any]:
    task = task_registry.get(payload.task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Unknown task_id")

    try:
        stroke_payload = json.loads(payload.content)
        strokes = [Stroke.model_validate(item) for item in stroke_payload]
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid stroke JSON content") from exc

    image_png = rasterize_strokes_to_png(strokes)
    try:
        analysis = llm_service.analyse_student_work(task.question, image_png)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return success_response(analysis.model_dump())
