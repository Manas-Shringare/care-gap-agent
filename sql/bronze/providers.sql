CREATE EXTERNAL TABLE caregap_bronze.providers (
  `id` string,
  `organization` string,
  `name` string,
  `gender` string,
  `speciality` string,
  `address` string,
  `city` string,
  `state` string,
  `zip` string,
  `lat` string,
  `lon` string,
  `utilization` string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES ('separatorChar' = ',', 'quoteChar' = '"', 'escapeChar' = '\\')
LOCATION 's3://__DATA_BUCKET__/bronze/providers/'
TBLPROPERTIES ('skip.header.line.count' = '1')
