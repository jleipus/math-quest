from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.config import get_settings
from backend.models.common import error_response
from backend.routers.assistant import router as assistant_router
from backend.routers.curriculum import router as curriculum_router
from backend.routers.tasks import router as tasks_router

settings = get_settings()

app = FastAPI(title=settings.app_name, version=settings.app_version)

api_prefix = "/api/v1"
app.include_router(tasks_router, prefix=api_prefix)
app.include_router(curriculum_router, prefix=api_prefix)
app.include_router(assistant_router, prefix=api_prefix)


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(code="HTTP_ERROR", message=str(exc.detail)),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    first_error = exc.errors()[0] if exc.errors() else {"msg": "Invalid request"}
    message = first_error.get("msg", "Invalid request")
    return JSONResponse(
        status_code=422,
        content=error_response(code="VALIDATION_ERROR", message=message),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=error_response(code="INTERNAL_SERVER_ERROR", message="Something went wrong."),
    )
