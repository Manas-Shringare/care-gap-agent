SELECT code, description, units, count(*) AS n, min(value) AS example_min, max(value) AS example_max
FROM caregap_silver.observations
WHERE "type" = 'text' AND value_num IS NOT NULL
GROUP BY 1, 2, 3
ORDER BY n DESC
LIMIT 15