# Dataset: dog-images

**Real photographs, not synthetic** — used for the Dog image classifier (M14 follow-up, see
`docs/specs/M14-dog-disease-detection.md`).

## Source

[Pet Disease images](https://www.kaggle.com/datasets/smadive/pet-disease-images) (Kaggle,
`smadive`), downloaded via `kagglehub.dataset_download(...)` — no Kaggle account/API token
required for this public dataset. This is a large multi-species dataset (22 folders across Cat
and Dog); only the 4 Dog folders below are used here.

## Classes

293 images total, 4 classes (unbalanced — real data, not padded to match) — folder name →
`DISEASES` label in `app/models/dog_image_model.py`:

| Folder | `DISEASES` label | Images |
|---|---|---|
| `distemper/` | `Canine Distemper` | 58 |
| `parvovirus/` | `Canine Parvovirus` | 82 |
| `kennel-cough/` | `Kennel Cough` | 82 |
| `mange/` | `Mange` | 71 |

Matches M14's originally-researched disease list closely (canine distemper, canine parvovirus,
kennel cough, mange — see `docs/specs/M14-dog-disease-detection.md`).

**No "Healthy" photos exist for Dog in this dataset, or in anything else found across any
session.** The trained model always names one of these 4 diseases — it has no way to say a dog
is healthy. This is a real, disclosed limitation, not an oversight — see the "Follow-up"
section in `docs/specs/M14-dog-disease-detection.md` and `docs/DISCLAIMER.md`.

This same source has 7 more Dog-specific disease classes (Dental Disease, Eye Infection, Fungal
Infection, Hot Spots, Skin Allergy, Tick Infestation, Worm Infection — 69–103 images each) — not
used this round, flagged as available follow-up.

## License

**Not verified** — same honesty bar as `cattle-images/SOURCE.md`; check the
[Kaggle listing](https://www.kaggle.com/datasets/smadive/pet-disease-images) directly before
any redistribution beyond this project's own local training use.

## Redownload

```python
import kagglehub
path = kagglehub.dataset_download("smadive/pet-disease-images")
```

Then copy `data/{Distemper in Dog,Parvovirus in Dog,Kennel Cough in Dog,Mange in Dog}/` into
this directory as `{distemper,parvovirus,kennel-cough,mange}/`.
