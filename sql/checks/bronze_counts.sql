SELECT 'allergies' AS t, count(*) AS n FROM caregap_bronze.allergies UNION ALL
SELECT 'careplans', count(*) FROM caregap_bronze.careplans UNION ALL
SELECT 'conditions', count(*) FROM caregap_bronze.conditions UNION ALL
SELECT 'encounters', count(*) FROM caregap_bronze.encounters UNION ALL
SELECT 'immunizations', count(*) FROM caregap_bronze.immunizations UNION ALL
SELECT 'medications', count(*) FROM caregap_bronze.medications UNION ALL
SELECT 'observations', count(*) FROM caregap_bronze.observations UNION ALL
SELECT 'organizations', count(*) FROM caregap_bronze.organizations UNION ALL
SELECT 'patients', count(*) FROM caregap_bronze.patients UNION ALL
SELECT 'procedures', count(*) FROM caregap_bronze.procedures UNION ALL
SELECT 'providers', count(*) FROM caregap_bronze.providers
ORDER BY t