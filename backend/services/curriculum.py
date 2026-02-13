import threading
import time
from typing import Any

import requests
from bs4 import BeautifulSoup

from backend.config import get_settings
from backend.models.task import CurriculumTopic


class CurriculumService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cached_topics: list[CurriculumTopic] = []
        self._cache_time: float = 0.0

    def get_topics(self) -> list[CurriculumTopic]:
        settings = get_settings()
        now = time.time()

        with self._lock:
            if self._cached_topics and (now - self._cache_time) < settings.curriculum_cache_ttl_seconds:
                return self._cached_topics

        fetched = self._fetch_topics_from_source(settings.curriculum_source_url)

        with self._lock:
            self._cached_topics = fetched
            self._cache_time = time.time()
            return self._cached_topics

    def _fetch_topics_from_source(self, source_url: str) -> list[CurriculumTopic]:
        try:
            response = requests.get(source_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            topics = self._extract_topics(soup)
            if topics:
                return topics
        except requests.RequestException:
            pass

        return self._fallback_topics()

    def _extract_topics(self, soup: BeautifulSoup) -> list[CurriculumTopic]:
        candidate_titles: list[str] = []

        for selector in ("h1", "h2", "h3", ".heading", "[class*='title']", "a"):
            for node in soup.select(selector):
                text = node.get_text(strip=True)
                if text and 3 <= len(text) <= 60:
                    candidate_titles.append(text)

        cleaned = self._dedupe_and_filter(candidate_titles)

        topics: list[CurriculumTopic] = []
        for index, title in enumerate(cleaned[:20], start=1):
            topic_id = f"topic-{index}"
            topics.append(
                CurriculumTopic(
                    id=topic_id,
                    name=title,
                    subtopics=[f"Practice {title.lower()}", f"Word problems with {title.lower()}"],
                    grade_level="Mellanstadiet",
                )
            )
        return topics

    @staticmethod
    def _dedupe_and_filter(items: list[str]) -> list[str]:
        seen: set[str] = set()
        filtered: list[str] = []

        for value in items:
            normalized = " ".join(value.split()).strip()
            lower = normalized.lower()
            if lower in seen:
                continue
            if any(skip in lower for skip in ["cookie", "integritet", "kontakt", "meny", "logga in"]):
                continue
            seen.add(lower)
            filtered.append(normalized)

        return filtered

    @staticmethod
    def _fallback_topics() -> list[CurriculumTopic]:
        fallback: list[dict[str, Any]] = [
            {
                "id": "addition",
                "name": "Addition",
                "subtopics": ["Adding whole numbers", "Carrying over"],
                "grade_level": "Year 4-5",
            },
            {
                "id": "subtraction",
                "name": "Subtraction",
                "subtopics": ["Subtracting whole numbers", "Borrowing"],
                "grade_level": "Year 4-5",
            },
            {
                "id": "multiplication",
                "name": "Multiplication",
                "subtopics": ["Times tables", "Multi-digit multiplication"],
                "grade_level": "Year 4-6",
            },
            {
                "id": "fractions",
                "name": "Fractions",
                "subtopics": ["Equivalent fractions", "Adding fractions"],
                "grade_level": "Year 5-6",
            },
        ]
        return [CurriculumTopic.model_validate(item) for item in fallback]


curriculum_service = CurriculumService()
