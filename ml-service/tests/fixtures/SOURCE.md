# Test fixtures: non-animal photos

Two small real photos used by `test_species_gate.py` to verify the "is this even an animal"
gate (`app/models/species_gate.py`, see `docs/specs/M15-image-diagnosis-quality-gate.md`)
actually rejects genuinely non-animal content — a synthetic image (solid color, random
noise, geometric pattern) doesn't work for this: tested and confirmed all three pass the
gate anyway, since ~40% of ImageNet-1k's 1000 classes are animal classes, so a top-5 draw on
a degenerate/random input has a high chance of including one purely by chance. Real photos
with genuine, coherent visual structure are what actually needed for this test.

Unlike the large gitignored training datasets (`data/*-images/`), these are small (60-70KB)
functional test fixtures, not training data — committed directly rather than gitignored, so
this test actually runs in CI instead of being skipped for a missing local dataset.

## Source

Both from Wikimedia Commons (freely licensed by Commons' own hosting policy):

- `non-animal-table.jpg` — [Copped Hall dining room mock-up display](https://commons.wikimedia.org/wiki/File:Copped_Hall_dining_room_mock-up_display,_Epping,_Essex,_England_01.jpg)
- `non-animal-car.jpg` — [2005 Toyota Corolla](https://commons.wikimedia.org/wiki/File:2005_Toyota_Corolla_1.4_T3.jpg)
