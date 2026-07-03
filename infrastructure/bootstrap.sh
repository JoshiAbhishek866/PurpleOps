#!/bin/bash
# Run this ONCE before terraform init to create the remote state backend.
# Usage: bash infrastructure/bootstrap.sh

set -e

REGION="us-east-1"
STATE_BUCKET="purpleops-terraform-state"
LOCK_TABLE="purpleops-tf-lock"

echo "Creating S3 state bucket: $STATE_BUCKET"
aws s3 mb s3://$STATE_BUCKET --region $REGION

aws s3api put-bucket-versioning \
  --bucket $STATE_BUCKET \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-encryption \
  --bucket $STATE_BUCKET \
  --server-side-encryption-configuration '{
    "Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]
  }'

aws s3api put-public-access-block \
  --bucket $STATE_BUCKET \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

echo "Creating DynamoDB lock table: $LOCK_TABLE"
aws dynamodb create-table \
  --table-name $LOCK_TABLE \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region $REGION

echo "Bootstrap complete. Now run: cd infrastructure && terraform init"
