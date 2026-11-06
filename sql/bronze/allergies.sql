CREATE EXTERNAL TABLE caregap_bronze.allergies (
  `start` string,
  `stop` string,
  `patient` string,
  `encounter` string,
  `code` string,
  `system` string,
  `description` string,
  `type` string,
  `category` string,
  `reaction1` string,
  `description1` string,
  `severity1` string,
  `reaction2` string,
  `description2` string,
  `severity2` string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES ('separatorChar' = ',', 'quoteChar' = '"', 'escapeChar' = '\\')
LOCATION 's3://__DATA_BUCKET__/bronze/allergies/'
TBLPROPERTIES ('skip.header.line.count' = '1')
