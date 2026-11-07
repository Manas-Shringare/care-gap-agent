CREATE TABLE caregap_silver.organizations
WITH (
  format = 'PARQUET',
  write_compression = 'SNAPPY',
  external_location = 's3://__DATA_BUCKET__/silver/organizations/'
)
AS SELECT
  NULLIF("id", '') AS "id",
  NULLIF("name", '') AS "name",
  NULLIF("address", '') AS "address",
  NULLIF("city", '') AS "city",
  NULLIF("state", '') AS "state",
  NULLIF("zip", '') AS "zip",
  CAST(NULLIF("lat", '') AS double) AS "lat",
  CAST(NULLIF("lon", '') AS double) AS "lon",
  NULLIF("phone", '') AS "phone",
  CAST(NULLIF("revenue", '') AS double) AS "revenue",
  CAST(NULLIF("utilization", '') AS bigint) AS "utilization"
FROM caregap_bronze.organizations
