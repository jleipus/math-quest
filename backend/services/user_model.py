import os
from threading import Lock
from typing import Any

from backend.models.user_model import DifficultyRecord, TopicRecord


class UserModel:
    """Tracks attempts, hints, and correctness per topic and difficulty."""

    def __init__(self, topics: dict[str, TopicRecord] | None = None) -> None:
        self._topics: dict[str, TopicRecord] = topics or {}

    def _get_diff_record(self, topic: str, difficulty: str) -> DifficultyRecord:
        """Return (creating if needed) the DifficultyRecord for a topic+difficulty pair."""
        if topic not in self._topics:
            self._topics[topic] = TopicRecord(topic=topic, records={})
        topic_rec = self._topics[topic]
        if difficulty not in topic_rec.records:
            topic_rec.records[difficulty] = DifficultyRecord(topic=topic, difficulty=difficulty)
        return topic_rec.records[difficulty]

    def record_attempt(self, topic: str, correct: bool, difficulty: str) -> None:
        """Record one answer submission for a topic and difficulty."""
        rec = self._get_diff_record(topic, difficulty)
        rec.attempts += 1
        if correct:
            rec.correct += 1

    def record_hint(self, topic: str, difficulty: str) -> None:
        """Record one hint request for a topic and difficulty."""
        rec = self._get_diff_record(topic, difficulty)
        rec.hints += 1

    @property
    def records(self) -> list[TopicRecord]:
        return list(self._topics.values())

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict suitable for TinyDB storage."""
        return {
            topic: {
                "topic": tr.topic,
                "records": {
                    diff: {
                        "topic": dr.topic,
                        "difficulty": dr.difficulty,
                        "attempts": dr.attempts,
                        "hints": dr.hints,
                        "correct": dr.correct,
                    }
                    for diff, dr in tr.records.items()
                },
            }
            for topic, tr in self._topics.items()
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserModel":
        """Deserialise from a TinyDB-stored plain dict."""
        topics: dict[str, TopicRecord] = {}
        for topic, td in data.items():
            records = {diff: DifficultyRecord(**rd) for diff, rd in td.get("records", {}).items()}
            topics[topic] = TopicRecord(topic=td["topic"], records=records)
        return cls(topics=topics)

    def get_profile_context(self) -> str:
        """Return a plain-text summary of the student's performance for LLM context."""
        if not self._topics:
            return ""
        lines = ["Student performance profile:"]
        for topic_rec in self._topics.values():
            total_attempts = sum(r.attempts for r in topic_rec.records.values())
            total_correct = sum(r.correct for r in topic_rec.records.values())
            total_hints = sum(r.hints for r in topic_rec.records.values())
            note = " (struggling)" if total_attempts > 0 and total_hints >= total_attempts else ""
            lines.append(
                f"- {topic_rec.topic}: {total_attempts} attempts, "
                f"{total_correct} correct, {total_hints} hint(s){note}"
            )
            for diff_rec in topic_rec.records.values():
                if diff_rec.attempts > 0:
                    lines.append(
                        f"    {diff_rec.difficulty}: {diff_rec.attempts} attempts, "
                        f"{diff_rec.correct} correct, {diff_rec.hints} hint(s)"
                    )
        return "\n".join(lines)


class UserModelService:
    """Stores per-session UserModels, persisted to TinyDB."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._models: dict[str, UserModel] = {}
        self._db: Any = None  # TinyDB instance, opened lazily

    def _get_db(self) -> Any:
        """Open (or return cached) the TinyDB instance."""
        if self._db is None:
            from tinydb import TinyDB
            from backend.config import get_settings

            path = get_settings().user_model_db_path
            os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
            self._db = TinyDB(path)
        return self._db

    def _load(self, session_id: str) -> UserModel | None:
        """Load a UserModel from TinyDB; returns None if not found."""
        try:
            from tinydb import Query

            db = self._get_db()
            Session = Query()
            row = db.get(Session.session_id == session_id)
            if row is None:
                return None
            return UserModel.from_dict(row.get("topics", {}))
        except Exception:
            return None

    def _save(self, session_id: str, model: UserModel) -> None:
        """Upsert the UserModel for session_id into TinyDB."""
        try:
            from tinydb import Query

            db = self._get_db()
            Session = Query()
            db.upsert(
                {"session_id": session_id, "topics": model.to_dict()},
                Session.session_id == session_id,
            )
        except Exception:
            pass  # persistence failure must never crash the game

    def _get_or_create_unlocked(self, session_id: str) -> UserModel:
        """Return the UserModel for session_id; caller must hold _lock."""
        if session_id not in self._models:
            loaded = self._load(session_id)
            self._models[session_id] = loaded if loaded is not None else UserModel()
        return self._models[session_id]

    def get_or_create(self, session_id: str) -> UserModel:
        with self._lock:
            return self._get_or_create_unlocked(session_id)

    def record_attempt(self, session_id: str, topic: str, correct: bool, difficulty: str) -> None:
        """Record an attempt and immediately persist."""
        with self._lock:
            model = self._get_or_create_unlocked(session_id)
            model.record_attempt(topic=topic, correct=correct, difficulty=difficulty)
            self._save(session_id, model)

    def record_hint(self, session_id: str, topic: str, difficulty: str) -> None:
        """Record a hint request and immediately persist."""
        with self._lock:
            model = self._get_or_create_unlocked(session_id)
            model.record_hint(topic=topic, difficulty=difficulty)
            self._save(session_id, model)


user_model_service = UserModelService()
