#!/usr/bin/env bash
# Run one SQL statement from a file in the Athena workgroup; print status and results.
set -euo pipefail
FILE="${1:?usage: athena_run.sh <file.sql>}"
: "${DATA_BUCKET:?export DATA_BUCKET first}"
WG="${WORKGROUP:-caregap}"

SQL=$(sed "s/__DATA_BUCKET__/${DATA_BUCKET}/g" "$FILE")
QID=$(aws athena start-query-execution --work-group "$WG" \
        --query-string "$SQL" --query QueryExecutionId --output text)

while :; do
  STATE=$(aws athena get-query-execution --query-execution-id "$QID" \
            --query QueryExecution.Status.State --output text)
  case "$STATE" in QUEUED|RUNNING) sleep 1 ;; *) break ;; esac
done

echo "== $FILE: $STATE"
aws athena get-query-execution --query-execution-id "$QID" --output table --query \
  'QueryExecution.{reason:Status.StateChangeReason,scanned_bytes:Statistics.DataScannedInBytes,ms:Statistics.TotalExecutionTimeInMillis}'
if [ "$STATE" = "SUCCEEDED" ]; then
  aws athena get-query-results --query-execution-id "$QID" --max-items 50 \
    --query 'ResultSet.Rows[*].Data[*].VarCharValue' --output text
fi
[ "$STATE" = "SUCCEEDED" ]
