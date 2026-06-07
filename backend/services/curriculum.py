from threading import Lock
from typing import Any

from backend.config import get_settings
from backend.models.curriculum import Grade


class CurriculumService:
    """Provides curriculum data from TinyDB (tree) and ChromaDB (RAG)."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._db: Any = None  # TinyDB instance
        self._chroma_client: Any = None  # ChromaDB client
        self._tree: list[Grade] | None = None  # parsed curriculum tree (static)

    def get_grades(self) -> list[str]:
        """Return grade names from TinyDB.

        Returns:
            List of grade name strings.

        Raises:
            RuntimeError: If the tree database is unavailable or empty.
        """
        grades = self._load_tree()
        if not grades:
            raise RuntimeError("Curriculum tree database is empty or unavailable. Run index_curriculum first.")
        return [g.name for g in grades]

    def get_all_topics(self, grade_name: str) -> list[str]:
        """Return all topic names for the given grade.

        Args:
            grade_name: Grade name as stored in TinyDB.

        Returns:
            List of topic name strings.

        Raises:
            RuntimeError: If the grade is not found or has no topics.
        """
        grades = self._load_tree()
        grade = next((g for g in grades if g.name == grade_name), None)
        if not grade or not grade.topics:
            raise RuntimeError(f"No topics found for grade {grade_name!r}.")
        return [t.name for t in grade.topics]

    def retrieve_context(self, grade: str, topic: str, question: str, top_k: int | None = None) -> str:
        """Query ChromaDB for lesson text relevant to the grade, topic, and question.

        Args:
            grade: Grade name for the query.
            topic: Topic name for the query.
            question: The student's question or task text.
            top_k: Number of chunks to retrieve; defaults to ``settings.rag_top_k``.

        Returns:
            Concatenated relevant lesson text.

        Raises:
            RuntimeError: If ChromaDB is unavailable or returns no results.
        """
        settings = get_settings()
        k = top_k if top_k is not None else settings.rag_top_k

        collection = self._get_chroma_collection()
        query_text = f"{topic}: {question}"

        # Filter to the requested grade so chunks from other grades are excluded.
        # Fall back to an unfiltered query if the grade has fewer than k indexed chunks
        # (ChromaDB raises an error when n_results exceeds the filtered result set size).
        try:
            results = collection.query(
                query_texts=[query_text],
                n_results=k,
                where={"grade": grade},
            )
        except Exception:
            results = collection.query(query_texts=[query_text], n_results=k)

        documents = results.get("documents", [[]])[0]
        if not documents:
            raise RuntimeError(f"No curriculum context found for {grade!r} / {topic!r}.")
        return "\n\n".join(documents)

    def _get_db(self) -> Any:
        """Return the shared TinyDB instance, opening it lazily on first call."""
        if self._db is None:
            from tinydb import TinyDB

            settings = get_settings()
            self._db = TinyDB(settings.tiny_db_path)
        return self._db

    def _load_tree(self) -> list[Grade]:
        """Return the curriculum tree, parsing it from TinyDB on first call.

        The tree is static (rebuilt only by ``index_curriculum``), so it is
        cached in memory after the first load to avoid re-reading and
        re-validating every row on each request.

        Raises:
            RuntimeError: If the database cannot be opened or parsed.
        """
        if self._tree is not None:
            return self._tree
        try:
            with self._lock:
                if self._tree is None:  # double-checked locking
                    rows = self._get_db().all()
                    self._tree = [Grade.model_validate(row) for row in rows]
            return self._tree
        except Exception as exc:
            raise RuntimeError(f"Failed to load curriculum tree: {exc}") from exc

    def _get_chroma_collection(self) -> Any:
        """Return the shared ChromaDB curriculum collection.

        Raises:
            RuntimeError: If ChromaDB cannot be initialised.
        """
        try:
            if self._chroma_client is None:
                import chromadb

                settings = get_settings()
                with self._lock:
                    if self._chroma_client is None:  # double-checked locking
                        self._chroma_client = chromadb.PersistentClient(path=settings.chroma_db_path)
            return self._chroma_client.get_or_create_collection("curriculum")
        except Exception as exc:
            raise RuntimeError(f"Failed to initialise ChromaDB: {exc}") from exc


curriculum_service = CurriculumService()
