CREATE TABLE caregap_silver.careplans
WITH (
  format = 'PARQUET',
  write_compression = 'SNAPPY',
  external_location = 's3://__DATA_BUCKET__/silver/careplans/'
)
AS SELECT
  NULLIF("id", '') AS "id",
  CAST(NULLIF("start", '') AS date) AS "start",
  CAST(NULLIF("stop", '') AS date) AS "stop",
  NULLIF("patient", '') AS "patient",
  NULLIF("encounter", '') AS "encounter",
  NULLIF("code", '') AS "code",
  NULLIF("description", '') AS "description",
  NULLIF("reasoncode", '') AS "reasoncode",
  NULLIF("reasondescription", '') AS "reasondescription"
FROM caregap_bronze.careplans
