CREATE TABLE caregap_silver.medications
WITH (
  format = 'PARQUET',
  write_compression = 'SNAPPY',
  external_location = 's3://__DATA_BUCKET__/silver/medications/'
)
AS SELECT
  CAST(from_iso8601_timestamp(NULLIF("start", '')) AS timestamp) AS "start",
  CAST(from_iso8601_timestamp(NULLIF("stop", '')) AS timestamp) AS "stop",
  NULLIF("patient", '') AS "patient",
  NULLIF("payer", '') AS "payer",
  NULLIF("encounter", '') AS "encounter",
  NULLIF("code", '') AS "code",
  NULLIF("description", '') AS "description",
  CAST(NULLIF("base_cost", '') AS double) AS "base_cost",
  CAST(NULLIF("payer_coverage", '') AS double) AS "payer_coverage",
  CAST(NULLIF("dispenses", '') AS bigint) AS "dispenses",
  CAST(NULLIF("totalcost", '') AS double) AS "totalcost",
  NULLIF("reasoncode", '') AS "reasoncode",
  NULLIF("reasondescription", '') AS "reasondescription"
FROM caregap_bronze.medications
