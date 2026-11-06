CREATE EXTERNAL TABLE caregap_bronze.observations (
  `date` string,
  `patient` string,
  `encounter` string,
  `category` string,
  `code` string,
  `description` string,
  `value` string,
  `units` string,
  `type` string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES ('separatorChar' = ',', 'quoteChar' = '"', 'escapeChar' = '\\')
LOCATION 's3://__DATA_BUCKET__/bronze/observations/'
TBLPROPERTIES ('skip.header.line.count' = '1')
