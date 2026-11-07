CREATE TABLE caregap_silver.immunizations
WITH (
  format = 'PARQUET',
  write_compression = 'SNAPPY',
  external_location = 's3://__DATA_BUCKET__/silver/immunizations/'
)
AS SELECT
  CAST(from_iso8601_timestamp(NULLIF("date", '')) AS timestamp) AS "date",
  NULLIF("patient", '') AS "patient",
  NULLIF("encounter", '') AS "encounter",
  NULLIF("code", '') AS "code",
  NULLIF("description", '') AS "description",
  CAST(NULLIF("base_cost", '') AS double) AS "base_cost"
FROM caregap_bronze.immunizations
