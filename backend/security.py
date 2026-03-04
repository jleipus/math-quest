import secrets
from threading import Lock

from fastapi import Header, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.config import get_settings

limiter = Limiter(key_func=get_remote_address)


def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Validates the X-API-Key header when DAIS_API_KEY is set."""
    expected = get_settings().api_key
    if expected is None:
        return
    if x_api_key is None or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


_token_store: dict[str, str] = {}  # session_id -> session_token
_store_lock = Lock()


def create_session_token(session_id: str) -> str:
    """Generate and store a random token for a session."""
    token = secrets.token_urlsafe(32)
    with _store_lock:
        _token_store[session_id] = token
    return token


def verify_session_token(
    session_id: str,
    x_session_token: str | None = Header(default=None),
) -> None:
    """Verifies if the X-Session-Token header matches the session."""
    with _store_lock:
        expected = _token_store.get(session_id)
    if expected is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if x_session_token is None or not secrets.compare_digest(x_session_token, expected):
        raise HTTPException(status_code=403, detail="Invalid or missing session token")


def delete_session_token(session_id: str) -> None:
    """Remove a session token when the session is cleaned up."""
    with _store_lock:
        _token_store.pop(session_id, None)
