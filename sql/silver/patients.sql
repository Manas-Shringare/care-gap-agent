CREATE TABLE caregap_silver.patients
WITH (
  format = 'PARQUET',
  write_compression = 'SNAPPY',
  external_location = 's3://__DATA_BUCKET__/silver/patients/'
)
AS SELECT
  NULLIF("id", '') AS "id",
  CAST(NULLIF("birthdate", '') AS date) AS "birthdate",
  CAST(NULLIF("deathdate", '') AS date) AS "deathdate",
  NULLIF("ssn", '') AS "ssn",
  NULLIF("drivers", '') AS "drivers",
  NULLIF("passport", '') AS "passport",
  NULLIF("prefix", '') AS "prefix",
  NULLIF("first", '') AS "first",
  NULLIF("last", '') AS "last",
  NULLIF("suffix", '') AS "suffix",
  NULLIF("maiden", '') AS "maiden",
  NULLIF("marital", '') AS "marital",
  NULLIF("race", '') AS "race",
  NULLIF("ethnicity", '') AS "ethnicity",
  NULLIF("gender", '') AS "gender",
  NULLIF("birthplace", '') AS "birthplace",
  NULLIF("address", '') AS "address",
  NULLIF("city", '') AS "city",
  NULLIF("state", '') AS "state",
  NULLIF("county", '') AS "county",
  NULLIF("zip", '') AS "zip",
  CAST(NULLIF("lat", '') AS double) AS "lat",
  CAST(NULLIF("lon", '') AS double) AS "lon",
  CAST(NULLIF("healthcare_expenses", '') AS double) AS "healthcare_expenses",
  CAST(NULLIF("healthcare_coverage", '') AS double) AS "healthcare_coverage"
FROM caregap_bronze.patients
