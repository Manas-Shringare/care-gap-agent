# Run with admin credentials, not the app's runtime user.

aws dynamodb create-table \
  --table-name caregap-audit \
  --attribute-definitions AttributeName=request_id,AttributeType=S AttributeName=sk,AttributeType=S \
  --key-schema AttributeName=request_id,KeyType=HASH AttributeName=sk,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1