CREATE EXTERNAL TABLE caregap_bronze.encounters (
  `id` string,
  `start` string,
  `stop` string,
  `patient` string,
  `organization` string,
  `provider` string,
  `payer` string,
  `encounterclass` string,
  `code` string,
  `description` string,
  `base_encounter_cost` string,
  `total_claim_cost` string,
  `payer_coverage` string,
  `reasoncode` string,
  `reasondescription` string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES ('separatorChar' = ',', 'quoteChar' = '"', 'escapeChar' = '\\')
LOCATION 's3://__DATA_BUCKET__/bronze/encounters/'
TBLPROPERTIES ('skip.header.line.count' = '1')
