# The markdown block/section parser that retrieval is built on. It used to live in
# app/rag/ingest.py, which fed Chroma; it now backs the direct file reads that replaced it
# (docs/specs/remove-databases.md). The parsing rules are unchanged.
from app.rag.retrieval import _parse_sections, _slugify

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
