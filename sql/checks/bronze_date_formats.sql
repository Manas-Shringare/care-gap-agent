-- Profile every date-like bronze column before typing it in silver.
-- len 10 = YYYY-MM-DD (date); len 20 = YYYY-MM-DDTHH:MM:SSZ (timestamp).
-- Each column must show exactly one length, matching gen_silver_ctas.py.
SELECT 'allergies.start' AS col, length("start") AS len, count(*) AS n FROM caregap_bronze.allergies WHERE "start" <> '' GROUP BY 2 UNION ALL
SELECT 'allergies.stop', length("stop"), count(*) FROM caregap_bronze.allergies WHERE "stop" <> '' GROUP BY 2 UNION ALL
SELECT 'careplans.start', length("start"), count(*) FROM caregap_bronze.careplans WHERE "start" <> '' GROUP BY 2 UNION ALL
SELECT 'careplans.stop', length("stop"), count(*) FROM caregap_bronze.careplans WHERE "stop" <> '' GROUP BY 2 UNION ALL
SELECT 'conditions.start', length("start"), count(*) FROM caregap_bronze.conditions WHERE "start" <> '' GROUP BY 2 UNION ALL
SELECT 'conditions.stop', length("stop"), count(*) FROM caregap_bronze.conditions WHERE "stop" <> '' GROUP BY 2 UNION ALL
SELECT 'encounters.start', length("start"), count(*) FROM caregap_bronze.encounters WHERE "start" <> '' GROUP BY 2 UNION ALL
SELECT 'encounters.stop', length("stop"), count(*) FROM caregap_bronze.encounters WHERE "stop" <> '' GROUP BY 2 UNION ALL
SELECT 'immunizations.date', length("date"), count(*) FROM caregap_bronze.immunizations WHERE "date" <> '' GROUP BY 2 UNION ALL
SELECT 'medications.start', length("start"), count(*) FROM caregap_bronze.medications WHERE "start" <> '' GROUP BY 2 UNION ALL
SELECT 'medications.stop', length("stop"), count(*) FROM caregap_bronze.medications WHERE "stop" <> '' GROUP BY 2 UNION ALL
SELECT 'observations.date', length("date"), count(*) FROM caregap_bronze.observations WHERE "date" <> '' GROUP BY 2 UNION ALL
SELECT 'patients.birthdate', length("birthdate"), count(*) FROM caregap_bronze.patients WHERE "birthdate" <> '' GROUP BY 2 UNION ALL
SELECT 'patients.deathdate', length("deathdate"), count(*) FROM caregap_bronze.patients WHERE "deathdate" <> '' GROUP BY 2 UNION ALL
SELECT 'procedures.start', length("start"), count(*) FROM caregap_bronze.procedures WHERE "start" <> '' GROUP BY 2 UNION ALL
SELECT 'procedures.stop', length("stop"), count(*) FROM caregap_bronze.procedures WHERE "stop" <> '' GROUP BY 2
ORDER BY 1, 2