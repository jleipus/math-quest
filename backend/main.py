import time

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.routers.agent import router as agent_router
from backend.routers.curriculum import router as curriculum_router
from backend.routers.game import router as game_router
from backend.routers.user_model import router as user_model_router
from backend.services.logger import log

settings = get_settings()

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_prefix = "/api/v1"
app.include_router(game_router, prefix=api_prefix)
app.include_router(agent_router, prefix=api_prefix)
app.include_router(curriculum_router, prefix=api_prefix)
app.include_router(user_model_router, prefix=api_prefix)


@app.middleware("http")
async def http_logging_middleware(request: Request, call_next) -> Response:
    start = time.perf_counter()
    response = await call_next(request)
    log(
        "http_request",
        {
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round((time.perf_counter() - start) * 1000, 1),
        },
    )
    return response
