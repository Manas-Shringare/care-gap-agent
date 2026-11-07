SELECT
  (SELECT count(*) FROM caregap_silver.patients WHERE deathdate IS NULL) AS living,
  (SELECT count(*) FROM caregap_silver.patients WHERE deathdate IS NOT NULL) AS deceased,
  (SELECT min("date") FROM caregap_silver.observations) AS first_obs,
  (SELECT max("date") FROM caregap_silver.observations) AS last_obs,
  (SELECT count(*) FROM caregap_silver.allergies WHERE "stop" IS NOT NULL) AS allergy_stops,
  (SELECT count(*) FROM caregap_silver.observations WHERE code = '4548-4' AND "type" <> 'numeric') AS a1c_not_numeric
