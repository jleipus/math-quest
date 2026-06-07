from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from backend.config import get_settings
from backend.routers.curriculum import router as curriculum_router
from backend.routers.game import router as game_router
from backend.routers.user_model import router as user_model_router
from backend.security import limiter
from backend.services.logger import set_log_file

settings = get_settings()

if settings.llm_log_path:
    set_log_file(settings.llm_log_path)


class CatchUnhandledMiddleware:
    """Convert unhandled exceptions into a JSON 500 response.

    Starlette's built-in ServerErrorMiddleware sits *outside* user middleware,
    so a true 500 never passes back through the CORS middleware and the browser
    reports a misleading "No 'Access-Control-Allow-Origin' header" error that
    masks the real failure. Catching here (inside the CORS layer) lets the 500
    response carry CORS headers so the actual error surfaces to the client.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def send_wrapper(message: dict) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            if response_started:
                # Headers already sent; can't replace the response safely.
                raise
            response = JSONResponse(status_code=500, content={"detail": "Internal server error"})
            await response(scope, receive, send)


app = FastAPI(title=settings.app_name, version=settings.app_version)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
app.add_middleware(SlowAPIMiddleware)

# Ensure unhandled 500s still pass back through CORS (added below) so the
# browser sees the real error instead of a misleading CORS failure.
app.add_middleware(CatchUnhandledMiddleware)

# CORS (added last so it stays the outermost layer and wraps every response,
# including the 500s produced by CatchUnhandledMiddleware above)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_prefix = "/api/v1"
app.include_router(game_router, prefix=api_prefix)
app.include_router(curriculum_router, prefix=api_prefix)
app.include_router(user_model_router, prefix=api_prefix)
