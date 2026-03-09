import json
import logging

from fastapi import HTTPException

logger = logging.getLogger(__name__)

_app = None


def _get_app():
    """Initialise and return the Firebase Admin app."""
    global _app
    if _app is not None:
        return _app

    import firebase_admin
    from firebase_admin import credentials

    from backend.config import get_settings

    settings = get_settings()

    if not settings.firebase_service_account_json:
        raise RuntimeError("DAIS_FIREBASE_SERVICE_ACCOUNT_JSON is not set. Firebase token verification is unavailable.")

    try:
        sa = json.loads(settings.firebase_service_account_json)
        cred = credentials.Certificate(sa)
        _app = firebase_admin.initialize_app(cred)
    except Exception as exc:
        raise RuntimeError(f"Failed to initialise Firebase Admin SDK: {exc}") from exc

    return _app


def verify_id_token(token: str) -> str:
    """Verify a Firebase ID token and return the uid."""
    try:
        from firebase_admin import auth

        _get_app()
        decoded = auth.verify_id_token(token)
        return decoded["uid"]
    except RuntimeError as exc:
        # Firebase not configured, fail open only in dev, fail closed otherwise
        logger.warning("Firebase not configured: %s", exc)
        raise HTTPException(status_code=503, detail="Auth service not configured.")
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {exc}")
