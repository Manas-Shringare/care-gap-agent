CREATE EXTERNAL TABLE caregap_bronze.conditions (
  `start` string,
  `stop` string,
  `patient` string,
  `encounter` string,
  `code` string,
  `description` string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES ('separatorChar' = ',', 'quoteChar' = '"', 'escapeChar' = '\\')
LOCATION 's3://__DATA_BUCKET__/bronze/conditions/'
TBLPROPERTIES ('skip.header.line.count' = '1')
