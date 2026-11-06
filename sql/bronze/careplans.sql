CREATE EXTERNAL TABLE caregap_bronze.careplans (
  `id` string,
  `start` string,
  `stop` string,
  `patient` string,
  `encounter` string,
  `code` string,
  `description` string,
  `reasoncode` string,
  `reasondescription` string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES ('separatorChar' = ',', 'quoteChar' = '"', 'escapeChar' = '\\')
LOCATION 's3://__DATA_BUCKET__/bronze/careplans/'
TBLPROPERTIES ('skip.header.line.count' = '1')
