from typing import Any

from pydantic import BaseModel


class ApiError(BaseModel):
    code: str
    message: str


class ApiEnvelope(BaseModel):
    data: Any = None
    error: ApiError | None = None


def success_response(data: Any) -> dict[str, Any]:
    return ApiEnvelope(data=data, error=None).model_dump()


def error_response(code: str, message: str) -> dict[str, Any]:
    return ApiEnvelope(data=None, error=ApiError(code=code, message=message)).model_dump()
