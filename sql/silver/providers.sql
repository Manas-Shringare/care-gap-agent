CREATE TABLE caregap_silver.providers
WITH (
  format = 'PARQUET',
  write_compression = 'SNAPPY',
  external_location = 's3://__DATA_BUCKET__/silver/providers/'
)
AS SELECT
  NULLIF("id", '') AS "id",
  NULLIF("organization", '') AS "organization",
  NULLIF("name", '') AS "name",
  NULLIF("gender", '') AS "gender",
  NULLIF("speciality", '') AS "speciality",
  NULLIF("address", '') AS "address",
  NULLIF("city", '') AS "city",
  NULLIF("state", '') AS "state",
  NULLIF("zip", '') AS "zip",
  CAST(NULLIF("lat", '') AS double) AS "lat",
  CAST(NULLIF("lon", '') AS double) AS "lon",
  CAST(NULLIF("utilization", '') AS bigint) AS "utilization"
FROM caregap_bronze.providers
