"""
Retrieval over the checked-in markdown reference docs.

This whole file used to be skipped unless `chromadb` was importable, which on Windows meant
it only ever ran in Docker. It reads files now (docs/specs/remove-databases.md), so it runs
everywhere — and the behaviour it locks in is the behaviour a farmer actually sees.
"""
from app.agent.graph import REPORTABLE_DISEASES
from app.rag.retrieval import DIAGNOSIS_TO_DOC_SLUG, get_precautions, retrieve


def test_retrieve_returns_the_matching_disease_document():
    results = retrieve("Foot and Mouth Disease", k=3)

    assert len(results) > 0
    assert all(r["source"] == "foot-and-mouth-disease" for r in results)
    assert all({"text", "source"} <= r.keys() for r in results)


def test_retrieve_different_diseases_return_different_sources():
    fmd = retrieve("Foot and Mouth Disease", k=1)
    mastitis = retrieve("Mastitis", k=1)

    assert fmd[0]["source"] == "foot-and-mouth-disease"
    assert mastitis[0]["source"] == "mastitis"


def test_retrieve_cannot_surface_a_different_disease():
    # Stricter than the similarity search this replaced, and deliberately so: an exact
    # lookup can't drag in a thematically-similar neighbour's text.
    for diagnosis, slug in DIAGNOSIS_TO_DOC_SLUG.items():
        for chunk in retrieve(diagnosis, k=5):
            assert chunk["source"] == slug


def test_retrieve_unknown_diagnosis_returns_empty_list():
    assert retrieve("Not A Real Disease") == []


def test_retrieve_missing_docs_directory_returns_empty_list(tmp_path):
    assert retrieve("Mastitis", docs_dir=tmp_path / "does-not-exist") == []


def test_retrieve_respects_k():
    assert len(retrieve("Foot and Mouth Disease", k=1)) == 1


def test_retrieve_never_surfaces_precautions_or_next_steps_chunks():
    # M10 put precautions/next-steps in the same documents retrieve() reads — they must stay
    # invisible to it, since that content is never meant to feed the LLM-grounded
    # explanation prompt (see docs/specs/M10-precautions-next-steps.md).
    for diagnosis in ("Foot and Mouth Disease", "Lumpy Skin Disease", "Mastitis"):
        for chunk in retrieve(diagnosis, k=10):
            assert "Contact your veterinarian" not in chunk["text"]
            assert "Isolate the affected animal" not in chunk["text"]


def test_get_precautions_returns_content_for_known_disease():
    result = get_precautions("Mastitis")

    assert len(result["precautions"]) > 0
    assert len(result["next_steps"]) > 0
    assert all(isinstance(item, str) and item for item in result["precautions"])


def test_get_precautions_reportable_diseases_always_advise_escalation():
    # The one thing this feature must never get wrong, per docs/DISCLAIMER.md: precautions
    # for a reportable disease must never read as "no action needed."
    for disease in REPORTABLE_DISEASES:
        result = get_precautions(disease)
        next_steps_text = " ".join(result["next_steps"]).lower()
        assert "vet" in next_steps_text or "authority" in next_steps_text or "authorities" in next_steps_text


def test_get_precautions_exact_text_survived_the_move_off_chroma():
    # Golden output, captured from the running Chroma-backed service before it was replaced.
    # The whole point of the change was that this text is identical afterwards.
    result = get_precautions("Foot and Mouth Disease")

    assert result["precautions"] == [
        "Isolate the affected animal from the rest of the herd immediately.",
        "Restrict movement of animals, people, vehicles, and equipment on and off the farm.",
        "Avoid moving other animals to or from the property until authorities give guidance.",
    ]
    assert result["next_steps"] == [
        "Contact your veterinarian or local animal health authority immediately — this is a "
        "reportable disease and must not be handled without official involvement.",
        "Do not wait for symptoms to worsen before seeking help; early reporting limits spread.",
        "Follow any quarantine or biosecurity instructions given by animal health authorities.",
    ]


def test_every_mapped_diagnosis_has_a_readable_document():
    # A mapping entry with no file behind it fails silently as empty guidance — exactly the
    # gap that shipped when PPR was added to REPORTABLE_DISEASES without its document.
    for diagnosis in DIAGNOSIS_TO_DOC_SLUG:
        result = get_precautions(diagnosis)
        assert result["precautions"], f"no precautions found for {diagnosis}"
        assert result["next_steps"], f"no next steps found for {diagnosis}"


def test_get_precautions_healthy_returns_preventive_guidance():
    result = get_precautions("Healthy")

    assert len(result["precautions"]) > 0
    assert len(result["next_steps"]) > 0


def test_get_precautions_uncertain_returns_hardcoded_guidance():
    result = get_precautions("uncertain")

    assert result["precautions"] == ["Keep monitoring the animal closely for any new or worsening symptoms."]
    assert result["next_steps"] == [
        "Provide more symptom details for a more confident prediction, or consult a vet directly."
    ]


def test_get_precautions_unknown_diagnosis_returns_empty_lists():
    assert get_precautions("Not A Real Disease") == {"precautions": [], "next_steps": []}


def test_get_precautions_missing_document_returns_empty_lists(tmp_path):
    # Never raises on a broken install — a diagnosis must not fail because guidance text
    # couldn't be read.
    result = get_precautions("Mastitis", docs_dir=tmp_path / "does-not-exist")

    assert result == {"precautions": [], "next_steps": []}
