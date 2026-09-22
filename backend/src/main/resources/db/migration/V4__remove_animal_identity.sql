-- Removes animal identity (tag number, farm ID, and the animal record itself) — see
-- docs/specs/remove-animal-identity.md. None of it ever reached ml-service, which has always
-- taken only symptoms/image/species. Never edit V1-V3 — see AGENTS.md.
--
-- `species` moves from `animal` onto `diagnosis_case`. It's the one part of the animal record
-- worth keeping: it decides which trained model ran, so a stored case can't be read correctly
-- without it.

ALTER TABLE diagnosis_case ADD COLUMN species VARCHAR(20);

-- Backfill from the animal each case already points at, while that join still exists. Doing
-- this before the column is dropped keeps historical cases honest rather than stamping them
-- all 'COW'.
UPDATE diagnosis_case
SET species = animal.species
FROM animal
WHERE diagnosis_case.animal_id = animal.id;

-- Defensive only: animal_id is NOT NULL with an FK to animal, so no orphan can exist today.
-- If one somehow did, it would block the NOT NULL constraint below.
UPDATE diagnosis_case SET species = 'COW' WHERE species IS NULL;

ALTER TABLE diagnosis_case ALTER COLUMN species SET NOT NULL;

DROP INDEX IF EXISTS idx_diagnosis_case_animal_id;
ALTER TABLE diagnosis_case DROP COLUMN animal_id;

DROP TABLE animal;
