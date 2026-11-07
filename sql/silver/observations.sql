CREATE TABLE caregap_silver.observations
WITH (
  format = 'PARQUET',
  write_compression = 'SNAPPY',
  external_location = 's3://__DATA_BUCKET__/silver/observations/'
)
AS SELECT
  CAST(from_iso8601_timestamp(NULLIF("date", '')) AS timestamp) AS "date",
  NULLIF("patient", '') AS "patient",
  NULLIF("encounter", '') AS "encounter",
  NULLIF("category", '') AS "category",
  NULLIF("code", '') AS "code",
  NULLIF("description", '') AS "description",
  NULLIF("value", '') AS "value",
  NULLIF("units", '') AS "units",
  NULLIF("type", '') AS "type",
  TRY_CAST(NULLIF("value", '') AS double) AS value_num
FROM caregap_bronze.observations
