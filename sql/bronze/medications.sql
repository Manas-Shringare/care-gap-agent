CREATE EXTERNAL TABLE caregap_bronze.medications (
  `start` string,
  `stop` string,
  `patient` string,
  `payer` string,
  `encounter` string,
  `code` string,
  `description` string,
  `base_cost` string,
  `payer_coverage` string,
  `dispenses` string,
  `totalcost` string,
  `reasoncode` string,
  `reasondescription` string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES ('separatorChar' = ',', 'quoteChar' = '"', 'escapeChar' = '\\')
LOCATION 's3://__DATA_BUCKET__/bronze/medications/'
TBLPROPERTIES ('skip.header.line.count' = '1')
