"""
Ingests ml-service/data/veterinary-reference/*.md into the Chroma collection retrieval.py
reads from. Run from ml-service/ (venv active): `python -m app.rag.ingest`.

See ml-service/data/veterinary-reference/SOURCE.md for what these documents are (and
aren't).
"""
from __future__ import annotations

from pathlib import Path

from app.rag.retrieval import DEFAULT_PERSIST_DIR, _get_collection

DEFAULT_DOCS_DIR = Path(__file__).resolve().parents[2] / "data" / "veterinary-reference"


def _chunk(text: str) -> list[str]:
    return [p.strip() for p in text.split("\n\n") if p.strip()]


def ingest(docs_dir: Path = DEFAULT_DOCS_DIR, persist_dir: Path = DEFAULT_PERSIST_DIR) -> int:
    collection = _get_collection(persist_dir)

    total_chunks = 0
    for doc_path in sorted(docs_dir.glob("*.md")):
        if doc_path.name == "SOURCE.md":
            continue

        chunks = _chunk(doc_path.read_text(encoding="utf-8"))
        if not chunks:
            continue

        ids = [f"{doc_path.stem}-{i}" for i in range(len(chunks))]
        metadatas = [{"source": doc_path.stem} for _ in chunks]
        collection.upsert(ids=ids, documents=chunks, metadatas=metadatas)
        total_chunks += len(chunks)
        print(f"Ingested {len(chunks)} chunk(s) from {doc_path.name}")

    return total_chunks


if __name__ == "__main__":
    from app.rag.retrieval import COLLECTION_NAME

    count = ingest()
    print(f"Done — {count} chunks in the '{COLLECTION_NAME}' collection at {DEFAULT_PERSIST_DIR}.")
