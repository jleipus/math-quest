import re
import sys
import time
from uuid import uuid4

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, ".")

from backend.config import get_settings  # noqa: E402

BASE_URL = "https://www.matteboken.se"
INDEX_URL = f"{BASE_URL}/lektioner/mellanstadiet"
_GRADE_HREF = re.compile(r"^/lektioner/mellanstadiet/skolar-\d+$")


def _abs_url(href: str) -> str:
    """Prepend BASE_URL to relative hrefs."""
    return BASE_URL + href if href.startswith("/") else href


def scrape_curriculum_tree(soup: BeautifulSoup) -> list[dict]:
    """Parse the nav menu from the index page into a grade/topic/subtopic tree."""
    grades: list[dict] = []
    for grade_a in soup.select("li.menulink > a[href]"):
        if not _GRADE_HREF.match(grade_a["href"]):
            continue

        grade_mp = grade_a.find_next_sibling("div", class_="mp-level")
        if not grade_mp:
            continue

        topics: list[dict] = []
        for topic_li in grade_mp.select("ul > li.menulink"):
            topic_a = topic_li.find("a", recursive=False)
            if not topic_a:
                continue

            topic_mp = topic_a.find_next_sibling("div", class_="mp-level")
            subtopics: list[dict] = []
            if topic_mp:
                for sub_a in topic_mp.select("ul > li.menupagelink > a[href]"):
                    subtopics.append({"name": sub_a.get_text(strip=True), "url": _abs_url(sub_a["href"])})

            topics.append(
                {
                    "name": topic_a.get_text(strip=True),
                    "url": _abs_url(topic_a["href"]),
                    "subtopics": subtopics,
                }
            )

        grades.append({"name": grade_a.get_text(strip=True), "url": _abs_url(grade_a["href"]), "topics": topics})

    return grades


def fetch_lesson_text(url: str) -> str:
    """Fetch a lesson page and return its cleaned body text."""
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"\tSKIP {url}: {exc}")
        return ""

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["nav", "footer", "script", "style", "header"]):
        tag.decompose()

    lines = [ln for ln in soup.get_text(separator="\n", strip=True).splitlines() if len(ln.strip()) > 20]
    return " ".join(lines)


def make_chunks(text: str, url: str, grade: str, topic: str, subtopic: str, max_chunk: int = 800) -> list[dict]:
    """Split text into fixed-size chunks with metadata.

    Args:
        text: Full lesson text.
        url: Source URL (used as metadata and chunk id prefix).
        grade: Grade name for metadata.
        topic: Topic name for metadata.
        subtopic: Subtopic/lesson name for metadata.
        max_chunk: Maximum characters per chunk.

    Returns:
        List of chunk dicts with ``id``, ``text``, and ``metadata``.
    """
    chunks = []
    for i in range(0, len(text), max_chunk):
        chunk = text[i : i + max_chunk].strip()
        if chunk:
            chunks.append(
                {
                    "id": str(uuid4()),
                    "text": chunk,
                    "metadata": {
                        "source": url,
                        "grade": grade,
                        "topic": topic,
                        "subtopic": subtopic,
                    },
                }
            )
    return chunks


def write_to_chroma(chunks: list[dict], chroma_dir: str) -> None:
    """Upsert text chunks into ChromaDB for RAG retrieval."""
    import chromadb

    client = chromadb.PersistentClient(path=chroma_dir)
    collection = client.get_or_create_collection("curriculum")

    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        collection.upsert(
            ids=[c["id"] for c in batch],
            documents=[c["text"] for c in batch],
            metadatas=[c["metadata"] for c in batch],
        )
        print(f"\tChromaDB: indexed batch {i // batch_size + 1} ({len(batch)} chunks)")


def write_to_tinydb(tree: list[dict], db_path: str) -> None:
    """Write the curriculum tree into TinyDB, one document per grade."""
    from tinydb import TinyDB

    db = TinyDB(db_path)
    db.drop_tables()
    db.insert_multiple(tree)
    print(f"\tTinyDB: wrote {len(tree)} elements to {db_path}")


def main() -> None:
    settings = get_settings()
    chroma_dir = settings.chroma_db_path
    tree_db_path = settings.tiiny_db_path

    print(f"Fetching index: {INDEX_URL}")
    resp = requests.get(INDEX_URL, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    print("Parsing curriculum tree from nav menu...")
    grades = scrape_curriculum_tree(soup)
    if not grades:
        print("No grades found - aborting.")
        sys.exit(1)

    # Collect all leaf lesson URLs for RAG scraping
    all_chunks: list[dict] = []
    for grade in grades:
        for topic in grade["topics"]:
            for sub in topic["subtopics"]:
                print(f"Scraping: {grade['name']} / {topic['name']} / {sub['name']}")
                text = fetch_lesson_text(sub["url"])
                if text:
                    chunks = make_chunks(text, sub["url"], grade["name"], topic["name"], sub["name"])
                    print(f"\t-> {len(chunks)} chunks")
                    all_chunks.extend(chunks)
                time.sleep(0.3)  # be polite

    print(f"\nTotal chunks: {len(all_chunks)}")
    write_to_chroma(all_chunks, chroma_dir)
    write_to_tinydb(grades, tree_db_path)
    print("Done.")


if __name__ == "__main__":
    main()
