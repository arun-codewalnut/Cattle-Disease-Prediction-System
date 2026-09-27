Training datasets go here — gitignored, so they're not in the repo. Download them with
`python -m training.fetch_datasets` (run from `ml-service/`; Cow Mastitis photos are separate,
see `cattle-images/SOURCE.md`). Only needed to retrain models or run the real-photo tests.

Each dataset folder keeps a tracked `SOURCE.md` with its source, license and class layout.
When adding a dataset, add a `SOURCE.md`, a `.gitignore` exception for it (copy the pattern
used for the others), and an entry in `training/fetch_datasets.py`.

`veterinary-reference/` is different: those documents are part of the app (precautions and
next steps) and are tracked in full.
