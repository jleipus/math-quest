import pytest

from backend.services.curriculum import CurriculumService


def _grade_row(name: str, topics: list[str]) -> dict:
    """A TinyDB row shaped like a serialised Grade."""
    return {
        "name": name,
        "url": f"http://x/{name}",
        "topics": [{"name": t, "url": f"http://x/{name}/{t}", "subtopics": []} for t in topics],
    }


class _FakeDB:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows
        self.calls = 0

    def all(self) -> list[dict]:
        self.calls += 1
        return self._rows


def _service_with(rows: list[dict]) -> tuple[CurriculumService, _FakeDB]:
    svc = CurriculumService()
    fake = _FakeDB(rows)
    svc._get_db = lambda: fake  # type: ignore[method-assign]
    return svc, fake


class TestTreeCache:
    def test_reads_db_only_once(self):
        svc, fake = _service_with([_grade_row("Skolår 4", ["Addition"])])
        svc.get_grades()
        svc.get_grades()
        assert fake.calls == 1  # parsed once, cached thereafter

    def test_get_grades_returns_names_in_order(self):
        svc, _ = _service_with([_grade_row("Skolår 4", ["Addition"]), _grade_row("Skolår 5", ["Bråk"])])
        assert svc.get_grades() == ["Skolår 4", "Skolår 5"]

    def test_get_grades_raises_when_empty(self):
        svc, _ = _service_with([])
        with pytest.raises(RuntimeError):
            svc.get_grades()


class TestGetAllTopics:
    def test_returns_topics_for_grade(self):
        svc, _ = _service_with([_grade_row("Skolår 4", ["Addition", "Subtraktion"])])
        assert svc.get_all_topics("Skolår 4") == ["Addition", "Subtraktion"]

    def test_raises_for_unknown_grade(self):
        svc, _ = _service_with([_grade_row("Skolår 4", ["Addition"])])
        with pytest.raises(RuntimeError):
            svc.get_all_topics("Skolår 9")
