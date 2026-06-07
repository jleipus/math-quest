from backend.services.firestore_user_model import FirestoreUserModelService
from backend.services.user_model import UserModel


def _offline_service(max_cached_users: int = 64) -> FirestoreUserModelService:
    """A service whose Firestore reads/writes are no-ops (cache-only)."""
    svc = FirestoreUserModelService(max_cached_users=max_cached_users)
    svc._load = lambda uid: None  # type: ignore[method-assign]  # unknown users start fresh
    svc._save = lambda uid, data: None  # type: ignore[method-assign]  # drop writes
    return svc


class TestCacheEviction:
    def test_caps_at_max_cached_users(self):
        svc = _offline_service(max_cached_users=2)
        for uid in ("a", "b", "c"):
            svc.get_or_create(uid)
        assert len(svc._cache) == 2

    def test_evicts_least_recently_used(self):
        svc = _offline_service(max_cached_users=2)
        svc.get_or_create("a")
        svc.get_or_create("b")
        svc.get_or_create("a")  # touch "a" -> "b" becomes least-recently-used
        svc.get_or_create("c")  # inserting "c" evicts "b"
        assert set(svc._cache.keys()) == {"a", "c"}

    def test_reset_removes_from_cache(self):
        svc = _offline_service()
        svc.get_or_create("a")
        svc.reset("a")
        assert "a" not in svc._cache


class TestCacheIdentity:
    def test_returns_same_instance_for_repeated_access(self):
        svc = _offline_service()
        assert svc.get_or_create("a") is svc.get_or_create("a")

    def test_recorded_attempt_persists_in_cache(self):
        svc = _offline_service()
        svc.record_attempt("a", topic="Addition", correct=True, difficulty="easy")
        rec = svc.get_or_create("a")._topics["Addition"].records["easy"]
        assert (rec.attempts, rec.correct) == (1, 1)


class TestDocRoundTrip:
    def test_to_doc_from_doc_preserves_counts(self):
        m = UserModel()
        m.record_attempt("Addition", correct=True, difficulty="easy")
        m.record_attempt("Addition", correct=False, difficulty="easy")
        m.record_hint("Addition", difficulty="easy")
        m.record_attempt("Division", correct=True, difficulty="hard")

        doc = FirestoreUserModelService._to_doc(m)
        restored = FirestoreUserModelService._from_doc({"topics": doc})

        easy = restored._topics["Addition"].records["easy"]
        assert (easy.attempts, easy.correct, easy.hints) == (2, 1, 1)
        hard = restored._topics["Division"].records["hard"]
        assert (hard.attempts, hard.correct, hard.hints) == (1, 1, 0)

    def test_empty_model_round_trips_to_empty(self):
        doc = FirestoreUserModelService._to_doc(UserModel())
        restored = FirestoreUserModelService._from_doc({"topics": doc})
        assert restored.records == []
