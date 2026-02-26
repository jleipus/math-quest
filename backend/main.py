from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.routers.agent import router as agent_router
from backend.routers.curriculum import router as curriculum_router
from backend.routers.game import router as game_router
from backend.routers.user_model import router as user_model_router

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
