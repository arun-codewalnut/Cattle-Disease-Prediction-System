-- Buffalo dropped as a supported species (see docs/specs/M11-buffalo-disease-detection.md's
-- "Superseded" note) — no usable buffalo symptom or image dataset was ever found, so it never
-- moved past a disclosed cow-model approximation. The `species` column has no DB-level
-- enum/CHECK constraint (enforced only at the Java/JPA level via Species.java), so this needs
-- no schema change — just clearing any existing 'BUFFALO' rows so they don't fail to
-- deserialize once the Java enum drops that value. Diagnosis cases are deleted first: no
-- ON DELETE CASCADE exists on diagnosis_case.animal_id (see V1__init.sql).

DELETE FROM diagnosis_case WHERE animal_id IN (SELECT id FROM animal WHERE species = 'BUFFALO');
DELETE FROM animal WHERE species = 'BUFFALO';
