#!/usr/bin/env bash
set -euo pipefail
BUCKET="${1:?usage: create_data_bucket.sh <globally-unique-bucket-name>}"
REGION=us-east-1

aws s3api create-bucket --bucket "$BUCKET" --region "$REGION"

aws s3api put-public-access-block --bucket "$BUCKET" \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

aws s3api put-bucket-encryption --bucket "$BUCKET" \
  --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

aws s3api put-bucket-lifecycle-configuration --bucket "$BUCKET" \
  --lifecycle-configuration '{"Rules":[{"ID":"expire-athena-results","Status":"Enabled","Filter":{"Prefix":"athena-results/"},"Expiration":{"Days":7},"AbortIncompleteMultipartUpload":{"DaysAfterInitiation":1}}]}'

POLICY=$(cat <<EOF
{"Version":"2012-10-17","Statement":[{"Sid":"DenyInsecureTransport","Effect":"Deny","Principal":"*","Action":"s3:*",
"Resource":["arn:aws:s3:::${BUCKET}","arn:aws:s3:::${BUCKET}/*"],
"Condition":{"Bool":{"aws:SecureTransport":"false"}}}]}
EOF
)
aws s3api put-bucket-policy --bucket "$BUCKET" --policy "$POLICY"