-- Checkpoint 1 query against the typed silver tables.
-- Expected: gap_patients = 24, never_tested = 0 (same as bronze and the Python script).
WITH alive AS (
  SELECT id FROM caregap_silver.patients
  WHERE deathdate IS NULL
),
diabetic AS (
  SELECT DISTINCT c.patient
  FROM caregap_silver.conditions c
  JOIN alive a ON a.id = c.patient
  WHERE c.code = '44054006'
),
last_a1c AS (
  SELECT patient, max(CAST("date" AS date)) AS last_date
  FROM caregap_silver.observations
  WHERE code = '4548-4'
  GROUP BY patient
)
SELECT count(*) AS gap_patients,
       count_if(l.last_date IS NULL) AS never_tested
FROM diabetic d
LEFT JOIN last_a1c l ON l.patient = d.patient
WHERE l.last_date IS NULL OR l.last_date < DATE '2021-05-19'