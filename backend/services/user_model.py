from threading import Lock

from backend.models.user_model import TopicRecord


class UserModel:
    """Tracks attempts, hints, and correctness per topic."""

    def __init__(self) -> None:
        self._topics: dict[str, TopicRecord] = {}

    def record_attempt(self, topic: str, correct: bool) -> None:
        """Record one answer submission for a topic."""
        rec = self._topics.setdefault(topic, TopicRecord(topic=topic))
        rec.attempts += 1
        if correct:
            rec.correct += 1

    def record_hint(self, topic: str) -> None:
        """Record one hint request for a topic."""
        rec = self._topics.setdefault(topic, TopicRecord(topic=topic))
        rec.hints += 1

    @property
    def records(self) -> list[TopicRecord]:
        return list(self._topics.values())

    def get_profile_context(self) -> str:
        """Return a plain-text summary of the student's performance for LLM context."""
        if not self._topics:
            return ""
        lines = ["Student performance profile:"]
        for rec in self._topics.values():
            note = " (struggling)" if rec.attempts > 0 and rec.hints >= rec.attempts else ""
            lines.append(f"- {rec.topic}: {rec.attempts} attempts, {rec.correct} correct, {rec.hints} hint(s){note}")
        return "\n".join(lines)


class UserModelService:
    """Stores per-session UserModels."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._models: dict[str, UserModel] = {}

    def get_or_create(self, session_id: str) -> UserModel:
        with self._lock:
            if session_id not in self._models:
                self._models[session_id] = UserModel()
            return self._models[session_id]


user_model_service = UserModelService()
