import threading
import time
from typing import Any

import requests
from bs4 import BeautifulSoup

from backend.config import get_settings
from backend.models.curriculum import CurriculumTopic


class CurriculumService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cached_topics: list[CurriculumTopic] = []
        self._cache_time: float = 0.0
        self._chroma_collection: Any = None
        self._chroma_ready = False

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

    def retrieve_context(self, topic: str, question: str, top_k: int | None = None) -> str:
        settings = get_settings()
        k = top_k if top_k is not None else settings.rag_top_k

        collection = self._get_chroma_collection()
        if collection is None:
            return self._fallback_context(topic)

        try:
            query = f"{topic}: {question}"
            results = collection.query(query_texts=[query], n_results=k)
            documents = results.get("documents", [[]])[0]
            if documents:
                return "\n\n".join(documents)
        except Exception:
            pass

        return self._fallback_context(topic)

    def _get_chroma_collection(self) -> Any:
        if self._chroma_ready:
            return self._chroma_collection

        with self._lock:
            if self._chroma_ready:
                return self._chroma_collection
            self._chroma_collection = self._init_chroma()
            self._chroma_ready = True
            return self._chroma_collection

    @staticmethod
    def _init_chroma() -> Any:
        try:
            import chromadb

            settings = get_settings()
            client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
            collection = client.get_or_create_collection("curriculum")
            return collection
        except Exception:
            return None

    @staticmethod
    def _fallback_context(topic: str) -> str:
        fallback_map: dict[str, str] = {
            "addition": (
                "Addition means putting numbers together. "
                "Start with the ones column, then move to tens. "
                "If the sum in a column is 10 or more, carry the extra to the next column."
            ),
            "subtraction": (
                "Subtraction means taking one number away from another. "
                "Work column by column from right to left. "
                "If the top digit is smaller, borrow from the next column."
            ),
            "multiplication": (
                "Multiplication is repeated addition. "
                "Use times tables to find products quickly. "
                "For larger numbers, multiply each digit and add the partial products."
            ),
            "fractions": (
                "A fraction has a numerator (top) and denominator (bottom). "
                "To add fractions with the same denominator, add the numerators and keep the denominator. "
                "To add fractions with different denominators, first find a common denominator."
            ),
        }
        topic_lower = topic.strip().lower()
        for key, context in fallback_map.items():
            if key in topic_lower:
                return context
        return (
            "Mathematics at the mellanstadiet level covers arithmetic, fractions, "
            "geometry, and basic problem solving. Work step by step."
        )

    def _fetch_topics_from_source(self, source_url: str) -> list[CurriculumTopic]:
        # try:
        #     response = requests.get(source_url, timeout=10)
        #     response.raise_for_status()
        #     soup = BeautifulSoup(response.text, "html.parser")

        #     topics = self._extract_topics(soup)
        #     if topics:
        #         return topics
        # except requests.RequestException:
        #     pass

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
