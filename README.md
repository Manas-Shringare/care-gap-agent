# Care-Gap-Agent

This is a care-gap assistant for clinic care coordinators which is built on AWS (Bedrock, Athena,
DynamoDB) over **synthetic** patient records from Synthea.

Example question: "Which of my diabetic patients haven't had an A1c test in 6 months?"

**Status: personal project, in progress.**
- Working: FastAPI service that calls Amazon Bedrock (Nova Lite) with request tracing; every request is stored in a DynamoDB audit table (fails closed if the write fails); Synthea sample data queryable in Athena, as raw CSV and as typed Parquet.
- Next: An agent with read-only SQL, role-based access, and an evaluation gate in CI.

**Data:** Synthetic only, but handled as if it were PHI. This project demonstrates
HIPAA-style patterns. It makes no compliance claim.

- Synthea 1K Sample Synthetic Patient Records, CSV from Nov 2021 (1,163 rows, 1,000 living): https://synthea.mitre.org/downloads
- The sample is a snapshot that ends on 2021-11-19, so "last N months" rules are measured from that date, not from today.
- SHA-256 for synthea_sample_data_csv_nov2021.zip (56 MB): 870b68a127f3570ca964e89e49dd3433cf3e7a27cc4079d2bff5f094be0a43c2

**Thank you for your time!**
