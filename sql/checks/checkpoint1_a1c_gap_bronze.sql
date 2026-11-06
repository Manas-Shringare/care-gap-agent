-- Checkpoint 1: living diabetics (SNOMED 44054006) with no A1c (LOINC 4548-4)
-- on or after 2021-05-19, i.e. 6 months before the dataset as-of date 2021-11-19.
-- Expected (local Python ground truth): gap_patients = 24, never_tested = 0.
WITH alive AS (
  SELECT id FROM caregap_bronze.patients
  WHERE coalesce(deathdate, '') = ''
),
diabetic AS (
  SELECT DISTINCT c.patient
  FROM caregap_bronze.conditions c
  JOIN alive a ON a.id = c.patient
  WHERE c.code = '44054006'
),
last_a1c AS (
  SELECT patient, max(substr("date", 1, 10)) AS last_date
  FROM caregap_bronze.observations
  WHERE code = '4548-4'
  GROUP BY patient
)
SELECT count(*) AS gap_patients,
       count_if(l.last_date IS NULL) AS never_tested
FROM diabetic d
LEFT JOIN last_a1c l ON l.patient = d.patient
WHERE l.last_date IS NULL OR l.last_date < '2021-05-19'