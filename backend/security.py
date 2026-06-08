from fastapi import Header, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


def verify_firebase_token(authorization: str | None = Header(default=None)) -> str | None:
    """Optional Firebase auth dependency."""
    if authorization is None:
        return None
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Malformed Authorization header. Expected: Bearer <firebase-id-token>",
        )
    token = authorization.removeprefix("Bearer ").strip()
    from backend.services.firebase import verify_id_token

    return verify_id_token(token)
