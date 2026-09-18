-- M11 (docs/specs/M11-buffalo-disease-detection.md): the domain generalizes beyond
-- cattle-only. Renames the table and its FK column, and adds `species` so a record can
-- say which animal it is. Never edit V1__init.sql — see AGENTS.md.

ALTER TABLE cattle RENAME TO animal;

ALTER TABLE animal ADD COLUMN species VARCHAR(20) NOT NULL DEFAULT 'COW';
ALTER TABLE animal ALTER COLUMN species DROP DEFAULT;

ALTER TABLE diagnosis_case RENAME COLUMN cattle_id TO animal_id;
ALTER INDEX idx_diagnosis_case_cattle_id RENAME TO idx_diagnosis_case_animal_id;
