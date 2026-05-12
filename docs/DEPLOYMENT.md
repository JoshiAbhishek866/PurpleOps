# Deployment Guide

## Prerequisites

1. AWS Account with appropriate permissions
2. AWS CLI configured
3. Docker installed
4. Python 3.11+
5. Node.js 18+ (for frontend)

## Local Development

### 1. Clone Repository

```bash
git clone <repository-url>
cd sentinel-ai
```

### 2. Set Up Python Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your AWS credentials
```

### 4. Run Locally

```bash
python src/main.py
```

API will be available at `http://localhost:8000`

## AWS Deployment

### Option 1: AWS App Runner (Recommended)

1. **Build and Push Docker Image**

```bash
# Authenticate to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build image
docker build -t sentinel-ai .

# Tag image
docker tag sentinel-ai:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/sentinel-ai:latest

# Push to ECR
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/sentinel-ai:latest
```

2. **Create App Runner Service**

```bash
aws apprunner create-service \
  --service-name sentinel-ai \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/sentinel-ai:latest",
      "ImageRepositoryType": "ECR"
    },
    "AutoDeploymentsEnabled": true
  }' \
  --instance-configuration '{
    "Cpu": "1 vCPU",
    "Memory": "2 GB"
  }'
```

### Option 2: AWS CDK (Infrastructure as Code)

```bash
cd infrastructure
npm install
cdk bootstrap
cdk deploy
```

## Environment Variables

Required environment variables:

- `AWS_REGION`: AWS region (e.g., us-east-1)
- `BEDROCK_MODEL_ID`: Bedrock model ID
- `KNOWLEDGE_BASE_ID`: Knowledge base ID
- `DYNAMODB_TABLE_CAMPAIGNS`: DynamoDB table name
- `DYNAMODB_TABLE_AUDIT`: Audit log table name
- `S3_BUCKET_REPORTS`: S3 bucket for reports

## Post-Deployment

1. **Create DynamoDB Tables**

```bash
aws dynamodb create-table \
  --table-name CampaignSessions \
  --attribute-definitions \
    AttributeName=campaign_id,AttributeType=S \
    AttributeName=timestamp,AttributeType=N \
  --key-schema \
    AttributeName=campaign_id,KeyType=HASH \
    AttributeName=timestamp,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST
```

2. **Create S3 Bucket**

```bash
aws s3 mb s3://sentinel-ai-artifacts
aws s3api put-bucket-encryption \
  --bucket sentinel-ai-artifacts \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

3. **Enable Bedrock Access**

Ensure your AWS account has access to Amazon Bedrock and Claude 3.5 Sonnet model.

## Monitoring

- CloudWatch Logs: `/aws/apprunner/sentinel-ai`
- CloudWatch Metrics: App Runner metrics
- DynamoDB: Audit logs table

## Troubleshooting

### Issue: Bedrock Access Denied

Solution: Request model access in AWS Bedrock console

### Issue: DynamoDB Throttling

Solution: Switch to provisioned capacity or increase on-demand limits

### Issue: High Costs

Solution: Verify scale-to-zero is enabled and check Bedrock token usage
