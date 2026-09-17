"""
Chroma-backed retrieval for the agent's explain node. Runs embedded
(`chromadb.PersistentClient`) rather than against the separate networked `chroma` service
in docker-compose.yml — simpler, no server to coordinate, and easier to test (point at a
temp directory). See docs/specs/M6-rag-knowledge-base.md for why.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

COLLECTION_NAME = "veterinary_reference"

DEFAULT_PERSIST_DIR = Path(__file__).resolve().parents[2] / "data" / "chroma_db"

_collection_cache: dict[str, Any] = {}


def _get_collection(persist_dir: Path | None = None):
    # Imported lazily so importing this module doesn't require chromadb to be installed
    # unless retrieval is actually used — keeps ml-service importable in contexts that
    # don't touch RAG.
    import chromadb
    from chromadb.utils import embedding_functions

    path = str(persist_dir or DEFAULT_PERSIST_DIR)
    if path not in _collection_cache:
        client = chromadb.PersistentClient(path=path)
        _collection_cache[path] = client.get_or_create_collection(
            COLLECTION_NAME, embedding_function=embedding_functions.DefaultEmbeddingFunction()
        )
    return _collection_cache[path]


def retrieve(query: str, k: int = 3, persist_dir: Path | None = None) -> list[dict[str, str]]:
    """Returns up to k relevant chunks for `query`, each `{"text": ..., "source": ...}`.
    Returns [] (never raises) if the collection is empty or unreachable — retrieval failure
    must degrade gracefully, same principle as the explain node's LLM failure handling."""
    try:
        collection = _get_collection(persist_dir)
        count = collection.count()
        if count == 0:
            return []

        results = collection.query(query_texts=[query], n_results=min(k, count))
        documents = results.get("documents") or [[]]
        metadatas = results.get("metadatas") or [[]]

        return [
            {"text": doc, "source": meta.get("source", "unknown")}
            for doc, meta in zip(documents[0], metadatas[0])
        ]
    except Exception:
        return []
