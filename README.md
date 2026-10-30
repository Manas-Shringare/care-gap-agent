# Care-Gap-Agent

This is a care-gap assistant for clinic care coordinators which is built on AWS (Bedrock, Athena,
DynamoDB) over **synthetic** patient records from Synthea.

Example question: "Which of my diabetic patients haven't had an A1c test in 6 months?"

**Status: personal project, in progress.**
- Working: FastAPI service that calls Amazon Bedrock (Nova Lite) with request tracing.
- Next: Audit log in DynamoDB, Synthea data in Athena, an agent with read-only SQL,
  role-based access, and an evaluation gate in CI.

**Data:** Synthetic only, but handled as if it were PHI. This project demonstrates
HIPAA-style patterns. It makes no compliance claim.

**Thank you for your time!**