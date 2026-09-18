"""
Ingests ml-service/data/veterinary-reference/*.md into the Chroma collection retrieval.py
reads from. Run from ml-service/ (venv active): `python -m app.rag.ingest`.

See ml-service/data/veterinary-reference/SOURCE.md for what these documents are (and
aren't).
"""
from __future__ import annotations

import re
from pathlib import Path

from app.rag.retrieval import DEFAULT_PERSIST_DIR, _get_collection

DEFAULT_DOCS_DIR = Path(__file__).resolve().parents[2] / "data" / "veterinary-reference"

# Chunks under the title / before the first "## " heading are "overview" — the only section
# explain_node's retrieve() searches (see retrieval.py). A "## Heading" block sets the
# section for the blocks that follow it (M10) and isn't itself emitted as a chunk.
DEFAULT_SECTION = "overview"


def _slugify(heading: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", heading.strip().lower()).strip("-")


def _parse_sections(text: str) -> list[tuple[str, str]]:
    """Returns [(section, chunk_text), ...] — blocks separated by a blank line, with a
    "## Heading" block setting the section for subsequent blocks instead of becoming a
    chunk of its own."""
    section = DEFAULT_SECTION
    sections: list[tuple[str, str]] = []
    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        if block.startswith("## "):
            section = _slugify(block[3:])
            continue
        sections.append((section, block))
    return sections


def ingest(docs_dir: Path = DEFAULT_DOCS_DIR, persist_dir: Path = DEFAULT_PERSIST_DIR) -> int:
    collection = _get_collection(persist_dir)

    total_chunks = 0
    for doc_path in sorted(docs_dir.glob("*.md")):
        if doc_path.name == "SOURCE.md":
            continue

        sections = _parse_sections(doc_path.read_text(encoding="utf-8"))
        if not sections:
            continue

        ids = [f"{doc_path.stem}-{i}" for i in range(len(sections))]
        documents = [text for _, text in sections]
        metadatas = [{"source": doc_path.stem, "section": section} for section, _ in sections]
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        total_chunks += len(sections)
        print(f"Ingested {len(sections)} chunk(s) from {doc_path.name}")

    return total_chunks


if __name__ == "__main__":
    from app.rag.retrieval import COLLECTION_NAME

    count = ingest()
    print(f"Done — {count} chunks in the '{COLLECTION_NAME}' collection at {DEFAULT_PERSIST_DIR}.")
