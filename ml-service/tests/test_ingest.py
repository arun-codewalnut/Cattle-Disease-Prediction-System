# Pure parsing logic — no chromadb needed, so unlike test_rag_retrieval.py this runs
# natively on Windows too (ingest.py's chromadb usage is confined to _get_collection,
# called only from ingest(), never from _parse_sections/_slugify).
from app.rag.ingest import _parse_sections, _slugify

SAMPLE_DOC = """# Sample Disease

This is the overview paragraph.

It has two parts.

## Precautions

- Do this first.
- Then this.

## Next steps

- Call the vet.
"""


def test_slugify_lowercases_and_hyphenates():
    assert _slugify("Next steps") == "next-steps"
    assert _slugify("Precautions") == "precautions"


def test_parse_sections_tags_overview_before_first_heading():
    sections = _parse_sections(SAMPLE_DOC)

    overview_chunks = [text for section, text in sections if section == "overview"]
    assert overview_chunks == [
        "# Sample Disease",
        "This is the overview paragraph.",
        "It has two parts.",
    ]


def test_parse_sections_tags_content_under_each_heading():
    sections = _parse_sections(SAMPLE_DOC)

    assert ("precautions", "- Do this first.\n- Then this.") in sections
    assert ("next-steps", "- Call the vet.") in sections


def test_parse_sections_heading_blocks_are_not_emitted_as_chunks():
    sections = _parse_sections(SAMPLE_DOC)

    chunk_texts = [text for _, text in sections]
    assert "## Precautions" not in chunk_texts
    assert "## Next steps" not in chunk_texts


def test_parse_sections_empty_text_returns_empty_list():
    assert _parse_sections("") == []
    assert _parse_sections("   \n\n  ") == []
