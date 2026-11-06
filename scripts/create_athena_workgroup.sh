#!/usr/bin/env bash
set -euo pipefail
BUCKET="${1:?usage: create_athena_workgroup.sh <data-bucket>}"

aws athena create-work-group --name caregap \
  --description "care-gap-agent queries" \
  --configuration "{
    \"ResultConfiguration\": {
      \"OutputLocation\": \"s3://${BUCKET}/athena-results/\",
      \"EncryptionConfiguration\": {\"EncryptionOption\": \"SSE_S3\"}
    },
    \"EnforceWorkGroupConfiguration\": true,
    \"PublishCloudWatchMetricsEnabled\": false,
    \"BytesScannedCutoffPerQuery\": 1073741824,
    \"EngineVersion\": {\"SelectedEngineVersion\": \"AUTO\"}
  }"