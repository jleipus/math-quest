import secrets

from fastapi import Header, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.config import get_settings

limiter = Limiter(key_func=get_remote_address)


def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Validates the X-API-Key header when DAIS_API_KEY is set."""
    expected = get_settings().api_key
    if not expected or expected is "":
        return
    if x_api_key is None or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
