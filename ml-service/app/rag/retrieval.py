"""
Filesystem-backed retrieval over ml-service/data/veterinary-reference/*.md.

This used to run on Chroma (`chromadb.PersistentClient`, embedded). It was replaced with
direct file reads — see docs/specs/remove-databases.md. The corpus is six hand-written
documents totalling ~11 KB, and both callers address it by exact key: `get_precautions()`
was always a metadata lookup rather than a similarity search, and `retrieve()` was called
with the diagnosis name, which `DIAGNOSIS_TO_DOC_SLUG` already maps to a single document. A
vector index bought nothing at that size and cost a native dependency (`chroma-hnswlib`,
which has no cp313 wheel) that forced this service's tests through Docker.

Still RAG: the explain node retrieves documents and grounds the prompt in them. Only the
retrieval source changed.

Neither function raises. A missing directory, an unreadable file or an unknown diagnosis
gives empty results and the diagnosis continues — the same degradation Chroma failures had.
"""
from __future__ import annotations

import re
from pathlib import Path

DEFAULT_DOCS_DIR = Path(__file__).resolve().parents[2] / "data" / "veterinary-reference"

# Blocks before the first "## " heading. The only section the explain node's retrieve() sees,
# so precautions/next-steps content can never leak into the LLM-grounded explanation prompt
# (the M10 guarantee, previously enforced with a `where={"section": "overview"}` filter).
DEFAULT_SECTION = "overview"

# Exact (diagnosis -> document) map, never a fuzzy match, so guidance for one disease can
# never be shown for another — see docs/specs/M10-precautions-next-steps.md. Every entry in
# app/agent/graph.py's REPORTABLE_DISEASES must appear here: a reportable diagnosis with no
# guidance reads as "no action needed" (docs/DISCLAIMER.md).
DIAGNOSIS_TO_DOC_SLUG = {
    "Foot and Mouth Disease": "foot-and-mouth-disease",
    "Lumpy Skin Disease": "lumpy-skin-disease",
    "Mastitis": "mastitis",
    "Bovine Respiratory Disease": "bovine-respiratory-disease",
    "Healthy": "healthy",
    "PPR (Peste des Petits Ruminants)": "peste-des-petits-ruminants",
    # M16: Dog's retrained v2 model's disease list (docs/specs/M14-dog-disease-detection.md's
    # "Follow-up" section) and Goat's binary "Unhealthy" output.
    "Bacterial Dermatosis": "bacterial-dermatosis",
    "Fungal Infection": "fungal-infection",
    "Hypersensitivity/Allergic Dermatosis": "hypersensitivity-allergic-dermatosis",
    "Unhealthy": "unhealthy-goat",
}

# "uncertain" isn't a disease, so it has no reference doc — mirrors
# app/agent/graph.py's _template_explanation's hardcoded uncertain-case wording.
_UNCERTAIN_PRECAUTIONS = [
    "Keep monitoring the animal closely for any new or worsening symptoms.",
]
_UNCERTAIN_NEXT_STEPS = [
    "Provide more symptom details for a more confident prediction, or consult a vet directly.",
]

# Parsed documents, keyed by resolved path. The corpus is tiny, so this is a convenience
# rather than an optimisation — and unlike the old Chroma collection, editing a markdown file
# needs only a restart, not a re-ingest step.
_document_cache: dict[str, dict[str, list[str]]] = {}


def _slugify(heading: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", heading.strip().lower()).strip("-")


def _parse_sections(text: str) -> list[tuple[str, str]]:
    """Returns [(section, block_text), ...] — blocks separated by a blank line, with a
    "## Heading" block setting the section for subsequent blocks instead of becoming a
    block of its own."""
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


def _bullets(text: str) -> list[str]:
    return [line.strip().lstrip("-•").strip() for line in text.splitlines() if line.strip()]


def _load_document(slug: str, docs_dir: Path | None = None) -> dict[str, list[str]]:
    """Returns {section: [block, ...]} for one document, or {} if it can't be read."""
    path = (docs_dir or DEFAULT_DOCS_DIR) / f"{slug}.md"
    key = str(path)
    if key not in _document_cache:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return {}
        by_section: dict[str, list[str]] = {}
        for section, block in _parse_sections(text):
            by_section.setdefault(section, []).append(block)
        _document_cache[key] = by_section
    return _document_cache[key]


def retrieve(query: str, k: int = 3, docs_dir: Path | None = None) -> list[dict[str, str]]:
    """Returns up to k overview blocks for `query` (a diagnosis name), each
    `{"text": ..., "source": ...}`. Returns [] for anything without a reference document.

    Exact lookup rather than the similarity search this used to run: the caller passes a
    diagnosis, and the mapping to its document is already known, so searching for it could
    only ever do worse — a near-miss could surface a different disease's text."""
    slug = DIAGNOSIS_TO_DOC_SLUG.get(query)
    if slug is None:
        return []

    blocks = _load_document(slug, docs_dir).get(DEFAULT_SECTION, [])
    return [{"text": block, "source": slug} for block in blocks[:k]]


def get_precautions(diagnosis: str, docs_dir: Path | None = None) -> dict[str, list[str]]:
    """Returns {"precautions": [...], "next_steps": [...]} for a diagnosis, read verbatim
    from its reference document and never generated by the LLM — see
    docs/specs/M10-precautions-next-steps.md. Empty lists for an unknown diagnosis or an
    unreadable document; never raises."""
    if diagnosis == "uncertain":
        return {"precautions": list(_UNCERTAIN_PRECAUTIONS), "next_steps": list(_UNCERTAIN_NEXT_STEPS)}

    slug = DIAGNOSIS_TO_DOC_SLUG.get(diagnosis)
    if slug is None:
        return {"precautions": [], "next_steps": []}

    by_section = _load_document(slug, docs_dir)
    return {
        "precautions": _bullets("\n".join(by_section.get("precautions", []))),
        "next_steps": _bullets("\n".join(by_section.get("next-steps", []))),
    }
