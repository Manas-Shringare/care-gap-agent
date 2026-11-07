#!/usr/bin/env bash
set -euo pipefail
BUCKET="${1:?usage: create_athena_build_workgroup.sh <data-bucket>}"

aws athena create-work-group --name caregap-build \
  --description "admin builds (CTAS into silver); not for the agent" \
  --configuration "{
    \"ResultConfiguration\": {
      \"OutputLocation\": \"s3://${BUCKET}/athena-results/\",
      \"EncryptionConfiguration\": {\"EncryptionOption\": \"SSE_S3\"}
    },
    \"EnforceWorkGroupConfiguration\": false,
    \"PublishCloudWatchMetricsEnabled\": false,
    \"BytesScannedCutoffPerQuery\": 1073741824
  }"