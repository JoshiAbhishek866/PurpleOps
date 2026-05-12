# Sentinel AI - Infrastructure (Terraform)

Provisions all AWS resources for the Sentinel AI platform.

## Resources Created

| Resource | Description |
|---|---|
| `aws_apprunner_service` | API container hosting (scale-to-zero) |
| `aws_dynamodb_table` x3 | CampaignSessions, AuditLogs, AgentRegistry |
| `aws_s3_bucket` | Compliance reports & artifacts |
| `aws_kms_key` | Encryption at rest |
| `aws_iam_role` x3 | Red Agent, Blue Agent, Coordinator (least privilege) |
| `aws_cloudwatch_log_group` | Centralized logging |
| `aws_cloudwatch_metric_alarm` | Token usage alerting |

## Quick Start

```bash
# 1. Configure AWS credentials
aws configure

# 2. Initialize Terraform
cd infrastructure
terraform init

# 3. Review the plan
terraform plan -var-file="terraform.tfvars"

# 4. Deploy
terraform apply -var-file="terraform.tfvars"
```

## Sensitive Variables

Never commit secrets. Use environment variables instead:

```bash
export TF_VAR_knowledge_base_id="your-kb-id"
export TF_VAR_n8n_webhook_url="http://your-n8n/webhook"
```

## Environments

```bash
# Dev
terraform workspace new dev
terraform apply -var="environment=dev"

# Staging
terraform workspace new staging
terraform apply -var="environment=staging"

# Production
terraform workspace new prod
terraform apply -var="environment=prod"
```

## State Backend

Remote state is stored in S3. Create the bucket before first `terraform init`:

```bash
aws s3 mb s3://sentinel-ai-terraform-state --region us-east-1
aws dynamodb create-table \
  --table-name sentinel-ai-tf-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

## Destroy

```bash
terraform destroy -var-file="terraform.tfvars"
```
