import logging
from threading import Lock
from typing import Any

from backend.models.user_model import DifficultyRecord, TopicRecord
from backend.services.user_model import UserModel

logger = logging.getLogger(__name__)


def _get_db():
    """Return the Firestore client."""
    from firebase_admin import firestore
    from backend.services.firebase import _get_app

    _get_app()
    return firestore.client()


class FirestoreUserModelService:
    """Manages per-user UserModels backed by Firestore."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._cache: dict[str, UserModel] = {}

    @staticmethod
    def _to_doc(model: UserModel) -> dict[str, Any]:
        """Serialise UserModel to a Firestore-friendly dict."""
        return {
            topic: {
                diff: {
                    "attempts": rec.attempts,
                    "correct": rec.correct,
                    "hints": rec.hints,
                }
                for diff, rec in topic_rec.records.items()
            }
            for topic, topic_rec in model._topics.items()
        }

    @staticmethod
    def _from_doc(data: dict[str, Any]) -> UserModel:
        """Deserialise a Firestore document dict into a UserModel."""
        topics: dict[str, TopicRecord] = {}
        for topic, diffs in data.get("topics", {}).items():
            records = {
                diff: DifficultyRecord(
                    topic=topic,
                    difficulty=diff,
                    attempts=counts.get("attempts", 0),
                    correct=counts.get("correct", 0),
                    hints=counts.get("hints", 0),
                )
                for diff, counts in diffs.items()
            }
            topics[topic] = TopicRecord(topic=topic, records=records)
        return UserModel(topics=topics)

    def _load(self, uid: str) -> UserModel | None:
        try:
            doc = _get_db().collection("user_models").document(uid).get()
            if not doc.exists:  # type:ignore
                return None
            return self._from_doc(doc.to_dict() or {})  # type:ignore
        except Exception as exc:
            logger.warning("Firestore load failed for uid=%s: %s", uid, exc)
            return None

    def _save(self, uid: str, data: dict[str, Any]) -> None:
        """Write a snapshot dict to Firestore."""
        try:
            _get_db().collection("user_models").document(uid).set({"topics": data})
        except Exception as exc:
            logger.warning("Firestore save failed for uid=%s: %s", uid, exc)

    def _get_or_create_unlocked(self, uid: str) -> UserModel:
        if uid not in self._cache:
            loaded = self._load(uid)
            self._cache[uid] = loaded if loaded is not None else UserModel()
        return self._cache[uid]

    def get_or_create(self, uid: str) -> UserModel:
        with self._lock:
            return self._get_or_create_unlocked(uid)

    def record_attempt(self, uid: str, topic: str, correct: bool, difficulty: str) -> None:
        with self._lock:
            model = self._get_or_create_unlocked(uid)
            model.record_attempt(topic=topic, correct=correct, difficulty=difficulty)
            snapshot = self._to_doc(model)
        self._save(uid, snapshot)

    def record_hint(self, uid: str, topic: str, difficulty: str) -> None:
        with self._lock:
            model = self._get_or_create_unlocked(uid)
            model.record_hint(topic=topic, difficulty=difficulty)
            snapshot = self._to_doc(model)
        self._save(uid, snapshot)

    def reset(self, uid: str) -> None:
        with self._lock:
            self._cache.pop(uid, None)
        try:
            _get_db().collection("user_models").document(uid).delete()
        except Exception as exc:
            logger.warning("Firestore reset failed for uid=%s: %s", uid, exc)


firestore_user_model_service = FirestoreUserModelService()
