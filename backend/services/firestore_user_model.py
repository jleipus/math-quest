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

    def _save(self, uid: str, model: UserModel) -> None:
        try:
            _get_db().collection("user_models").document(uid).set(
                {"topics": self._to_doc(model)},
                merge=True,
            )
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
        self._save(uid, model)

    def record_hint(self, uid: str, topic: str, difficulty: str) -> None:
        with self._lock:
            model = self._get_or_create_unlocked(uid)
            model.record_hint(topic=topic, difficulty=difficulty)
        self._save(uid, model)

    def merge_anonymous_into_account(self, anon_uid: str, account_uid: str) -> None:
        """
        Merge an anonymous user's model into a signed-in account's model,
        then delete the anonymous document.
        Called after a successful anonymous→Google account link.
        """
        with self._lock:
            anon_model = self._get_or_create_unlocked(anon_uid)
            account_model = self._get_or_create_unlocked(account_uid)

            # Add each anonymous attempt/hint count into the account model
            for topic_rec in anon_model.records:
                for diff_rec in topic_rec.records.values():
                    for _ in range(diff_rec.attempts):
                        account_model.record_attempt(
                            topic=diff_rec.topic,
                            correct=False,  # we only have totals, not individual results
                            difficulty=diff_rec.difficulty,
                        )
                    # Adjust correct count directly (avoid double-counting)
                    if diff_rec.correct:
                        acct_rec = account_model._get_diff_record(diff_rec.topic, diff_rec.difficulty)
                        acct_rec.correct += diff_rec.correct
                        # record_attempt already added diff_rec.attempts, compensate
                        acct_rec.correct = min(acct_rec.correct, acct_rec.attempts)
                    for _ in range(diff_rec.hints):
                        account_model.record_hint(topic=diff_rec.topic, difficulty=diff_rec.difficulty)

            # Evict anonymous from cache
            self._cache.pop(anon_uid, None)

        # Persist account model and delete anonymous document
        self._save(account_uid, account_model)
        try:
            _get_db().collection("user_models").document(anon_uid).delete()
        except Exception as exc:
            logger.warning("Failed to delete anonymous Firestore doc uid=%s: %s", anon_uid, exc)


firestore_user_model_service = FirestoreUserModelService()
