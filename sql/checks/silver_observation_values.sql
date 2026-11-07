-- value_num is the one soft cast. Every row Synthea marks as numeric must parse.
-- Expected: for type = 'numeric', n = parsed. Some text rows also parse (8,888 in this sample: income answers, code 63586-2, plus 2 ferritin rows). value_num means "looks numeric"; filter by code before arithmetic.
SELECT "type", count(*) AS n, count(value_num) AS parsed
FROM caregap_silver.observations
GROUP BY "type"
ORDER BY "type"