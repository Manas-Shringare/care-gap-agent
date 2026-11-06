CREATE EXTERNAL TABLE caregap_bronze.patients (
  `id` string,
  `birthdate` string,
  `deathdate` string,
  `ssn` string,
  `drivers` string,
  `passport` string,
  `prefix` string,
  `first` string,
  `last` string,
  `suffix` string,
  `maiden` string,
  `marital` string,
  `race` string,
  `ethnicity` string,
  `gender` string,
  `birthplace` string,
  `address` string,
  `city` string,
  `state` string,
  `county` string,
  `zip` string,
  `lat` string,
  `lon` string,
  `healthcare_expenses` string,
  `healthcare_coverage` string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES ('separatorChar' = ',', 'quoteChar' = '"', 'escapeChar' = '\\')
LOCATION 's3://__DATA_BUCKET__/bronze/patients/'
TBLPROPERTIES ('skip.header.line.count' = '1')
