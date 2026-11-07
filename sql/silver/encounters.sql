CREATE TABLE caregap_silver.encounters
WITH (
  format = 'PARQUET',
  write_compression = 'SNAPPY',
  external_location = 's3://__DATA_BUCKET__/silver/encounters/'
)
AS SELECT
  NULLIF("id", '') AS "id",
  CAST(from_iso8601_timestamp(NULLIF("start", '')) AS timestamp) AS "start",
  CAST(from_iso8601_timestamp(NULLIF("stop", '')) AS timestamp) AS "stop",
  NULLIF("patient", '') AS "patient",
  NULLIF("organization", '') AS "organization",
  NULLIF("provider", '') AS "provider",
  NULLIF("payer", '') AS "payer",
  NULLIF("encounterclass", '') AS "encounterclass",
  NULLIF("code", '') AS "code",
  NULLIF("description", '') AS "description",
  CAST(NULLIF("base_encounter_cost", '') AS double) AS "base_encounter_cost",
  CAST(NULLIF("total_claim_cost", '') AS double) AS "total_claim_cost",
  CAST(NULLIF("payer_coverage", '') AS double) AS "payer_coverage",
  NULLIF("reasoncode", '') AS "reasoncode",
  NULLIF("reasondescription", '') AS "reasondescription"
FROM caregap_bronze.encounters
