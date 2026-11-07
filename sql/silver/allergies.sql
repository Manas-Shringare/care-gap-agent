CREATE TABLE caregap_silver.allergies
WITH (
  format = 'PARQUET',
  write_compression = 'SNAPPY',
  external_location = 's3://__DATA_BUCKET__/silver/allergies/'
)
AS SELECT
  CAST(NULLIF("start", '') AS date) AS "start",
  CAST(NULLIF("stop", '') AS date) AS "stop",
  NULLIF("patient", '') AS "patient",
  NULLIF("encounter", '') AS "encounter",
  NULLIF("code", '') AS "code",
  NULLIF("system", '') AS "system",
  NULLIF("description", '') AS "description",
  NULLIF("type", '') AS "type",
  NULLIF("category", '') AS "category",
  NULLIF("reaction1", '') AS "reaction1",
  NULLIF("description1", '') AS "description1",
  NULLIF("severity1", '') AS "severity1",
  NULLIF("reaction2", '') AS "reaction2",
  NULLIF("description2", '') AS "description2",
  NULLIF("severity2", '') AS "severity2"
FROM caregap_bronze.allergies
