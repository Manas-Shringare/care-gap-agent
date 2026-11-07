CREATE TABLE caregap_silver.conditions
WITH (
  format = 'PARQUET',
  write_compression = 'SNAPPY',
  external_location = 's3://__DATA_BUCKET__/silver/conditions/'
)
AS SELECT
  CAST(NULLIF("start", '') AS date) AS "start",
  CAST(NULLIF("stop", '') AS date) AS "stop",
  NULLIF("patient", '') AS "patient",
  NULLIF("encounter", '') AS "encounter",
  NULLIF("code", '') AS "code",
  NULLIF("description", '') AS "description"
FROM caregap_bronze.conditions
