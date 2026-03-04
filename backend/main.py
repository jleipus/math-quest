from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from backend.config import get_settings
from backend.routers.agent import router as agent_router
from backend.routers.curriculum import router as curriculum_router
from backend.routers.game import router as game_router
from backend.routers.user_model import router as user_model_router
from backend.security import limiter
from backend.services.logger import set_log_file

settings = get_settings()

if settings.llm_log_path:
    set_log_file(settings.llm_log_path)

app = FastAPI(title=settings.app_name, version=settings.app_version)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
app.add_middleware(SlowAPIMiddleware)

# CORS
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
