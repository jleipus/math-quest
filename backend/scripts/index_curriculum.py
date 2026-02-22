"""
Standalone script: scrape matteboken.se (mellanstadiet) and index content into ChromaDB.

Usage:
    python -m backend.scripts.index_curriculum

Environment variables (same as the main app, with DAIS_ prefix):
    DAIS_CHROMA_PERSIST_DIR  — where to write the ChromaDB data (default: ./data/chroma)
    DAIS_CURRICULUM_SOURCE_URL — base URL to scrape (default: matteboken.se mellanstadiet)
"""

import sys
import time
from uuid import uuid4

import requests
from bs4 import BeautifulSoup

# Allow running as `python -m backend.scripts.index_curriculum` from the repo root.
sys.path.insert(0, ".")

from backend.config import get_settings  # noqa: E402


def scrape_lesson_links(index_url: str) -> list[tuple[str, str]]:
    """Return list of (title, url) for each lesson linked from the index page."""
    print(f"Fetching index: {index_url}")
    response = requests.get(index_url, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    base = "https://www.matteboken.se"
    links: list[tuple[str, str]] = []
    seen: set[str] = set()

    for a in soup.find_all("a", href=True):
        href: str = a["href"]
        if "/lektioner/" not in href:
            continue
        if href.startswith("/"):
            href = base + href
        if href in seen:
            continue
        seen.add(href)
        title = a.get_text(strip=True) or href
        links.append((title, href))

    print(f"Found {len(links)} lesson links")
    return links


def extract_text_chunks(url: str, title: str, max_chunk: int = 800) -> list[dict]:
    """Fetch a lesson page and split body text into chunks."""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"  SKIP {url}: {exc}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove nav/footer/script noise
    for tag in soup(["nav", "footer", "script", "style", "header"]):
        tag.decompose()

    body_text = soup.get_text(separator="\n", strip=True)
    lines = [line for line in body_text.splitlines() if len(line.strip()) > 20]
    combined = " ".join(lines)

    chunks = []
    for i in range(0, len(combined), max_chunk):
        chunk_text = combined[i : i + max_chunk].strip()
        if chunk_text:
            chunks.append(
                {
                    "id": str(uuid4()),
                    "text": chunk_text,
                    "metadata": {"source": url, "title": title},
                }
            )
    return chunks


def index_into_chroma(chunks: list[dict], chroma_dir: str) -> None:
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
        print(f"  Indexed batch {i // batch_size + 1} ({len(batch)} chunks)")


def main() -> None:
    settings = get_settings()
    index_url = settings.curriculum_source_url
    chroma_dir = settings.chroma_persist_dir

    print(f"ChromaDB target: {chroma_dir}")

    links = scrape_lesson_links(index_url)
    if not links:
        print("No lesson links found — aborting.")
        sys.exit(1)

    all_chunks: list[dict] = []
    for title, url in links:
        print(f"Scraping: {title} ({url})")
        chunks = extract_text_chunks(url, title)
        print(f"  → {len(chunks)} chunks")
        all_chunks.extend(chunks)
        time.sleep(0.3)  # be polite

    if not all_chunks:
        print("No content scraped — aborting.")
        sys.exit(1)

    print(f"\nTotal chunks to index: {len(all_chunks)}")
    index_into_chroma(all_chunks, chroma_dir)
    print("Done.")


if __name__ == "__main__":
    main()
