CREATE EXTERNAL TABLE caregap_bronze.organizations (
  `id` string,
  `name` string,
  `address` string,
  `city` string,
  `state` string,
  `zip` string,
  `lat` string,
  `lon` string,
  `phone` string,
  `revenue` string,
  `utilization` string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES ('separatorChar' = ',', 'quoteChar' = '"', 'escapeChar' = '\\')
LOCATION 's3://__DATA_BUCKET__/bronze/organizations/'
TBLPROPERTIES ('skip.header.line.count' = '1')
