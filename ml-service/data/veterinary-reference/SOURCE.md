# Source: veterinary-reference

**These are original, hand-written educational summaries, not sourced from, scraped from,
or copied from any specific external document.**

## Why

M6's RAG knowledge base needed reference material about the four diagnosable diseases
(Foot and Mouth Disease, Lumpy Skin Disease, Mastitis, Bovine Respiratory Disease). No
confirmed freely-licensed veterinary corpus was readily available in this environment, and
reproducing real (likely copyrighted) veterinary textbook or journal content wouldn't be
appropriate. Each document here is instead a short, general factual summary — symptoms,
transmission, general management notes — written for this learning project, the same
reasoning as [ml-service/data/synthetic-symptom-dataset/SOURCE.md](../synthetic-symptom-dataset/SOURCE.md)'s
approach to M1's training data.

## What these are NOT

- Not sourced from any specific book, paper, or website.
- Not veterinary guidance, and not a substitute for it — see
  [docs/DISCLAIMER.md](../../../docs/DISCLAIMER.md). Real diagnosis and treatment decisions
  need a real vet.
- Not exhaustive — each is a short overview, not a comprehensive clinical reference.

## Files

- `foot-and-mouth-disease.md`
- `lumpy-skin-disease.md`
- `mastitis.md`
- `bovine-respiratory-disease.md`

## Regenerate the Chroma collection from these files

```bash
cd ml-service
python -m app.rag.ingest
```
