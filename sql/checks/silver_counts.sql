SELECT 'allergies' AS t, count(*) AS n FROM caregap_silver.allergies UNION ALL
SELECT 'careplans' AS t, count(*) AS n FROM caregap_silver.careplans UNION ALL
SELECT 'conditions' AS t, count(*) AS n FROM caregap_silver.conditions UNION ALL
SELECT 'encounters' AS t, count(*) AS n FROM caregap_silver.encounters UNION ALL
SELECT 'immunizations' AS t, count(*) AS n FROM caregap_silver.immunizations UNION ALL
SELECT 'medications' AS t, count(*) AS n FROM caregap_silver.medications UNION ALL
SELECT 'observations' AS t, count(*) AS n FROM caregap_silver.observations UNION ALL
SELECT 'organizations' AS t, count(*) AS n FROM caregap_silver.organizations UNION ALL
SELECT 'patients' AS t, count(*) AS n FROM caregap_silver.patients UNION ALL
SELECT 'procedures' AS t, count(*) AS n FROM caregap_silver.procedures UNION ALL
SELECT 'providers' AS t, count(*) AS n FROM caregap_silver.providers
ORDER BY t
