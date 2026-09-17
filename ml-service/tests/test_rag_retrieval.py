import pytest

# chromadb has no cp313 wheel on Windows (see ml-service/AGENTS.md) — skip this whole file
# cleanly (not an error) when it's not installed natively; run these via Docker instead.
pytest.importorskip("chromadb")

from app.rag.retrieval import retrieve  # noqa: E402


def test_retrieve_returns_relevant_chunk_for_known_disease():
    results = retrieve("Foot and Mouth Disease", k=3)

    assert len(results) > 0
    assert any(r["source"] == "foot-and-mouth-disease" for r in results)
    assert all({"text", "source"} <= r.keys() for r in results)


def test_retrieve_different_diseases_return_different_top_source():
    fmd_results = retrieve("Foot and Mouth Disease blisters mouth lesions", k=1)
    mastitis_results = retrieve("Mastitis udder swelling milk yield", k=1)

    assert fmd_results[0]["source"] == "foot-and-mouth-disease"
    assert mastitis_results[0]["source"] == "mastitis"


def test_retrieve_from_empty_collection_returns_empty_list(tmp_path):
    results = retrieve("anything", persist_dir=tmp_path / "empty-collection")

    assert results == []


def test_retrieve_never_raises_on_backend_error(monkeypatch):
    import app.rag.retrieval as retrieval_module

    def _broken_get_collection(persist_dir=None):
        raise RuntimeError("simulated Chroma failure")

    monkeypatch.setattr(retrieval_module, "_get_collection", _broken_get_collection)

    results = retrieve("anything")

    assert results == []
