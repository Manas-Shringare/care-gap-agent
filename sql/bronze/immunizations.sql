CREATE EXTERNAL TABLE caregap_bronze.immunizations (
  `date` string,
  `patient` string,
  `encounter` string,
  `code` string,
  `description` string,
  `base_cost` string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES ('separatorChar' = ',', 'quoteChar' = '"', 'escapeChar' = '\\')
LOCATION 's3://__DATA_BUCKET__/bronze/immunizations/'
TBLPROPERTIES ('skip.header.line.count' = '1')
