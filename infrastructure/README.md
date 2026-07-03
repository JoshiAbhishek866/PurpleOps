# PurpleOps - Infrastructure (Terraform)

Provisions all AWS resources for the PurpleOps platform.

## Files

| File | Description |
|---|---|
| `main.tf` | Core resources: DynamoDB, S3, KMS, IAM, App Runner, CloudWatch |
| `ecr.tf` | ECR repository for Docker images |
| `bedrock.tf` | Bedrock Knowledge Base + OpenSearch Serverless |
| `waf.tf` | AWS WAF with SQL injection, XSS, rate limiting rules |
| `cicd.tf` | CodePipeline: GitHub → CodeBuild → ECR → App Runner |
| `eventbridge.tf` | EventBridge rules to trigger Blue Agent on WAF anomalies |
| `variables.tf` | All input variables with validation |
| `outputs.tf` | All output values (URLs, ARNs, IDs) |
| `terraform.tfvars` | Non-sensitive variable values |
| `buildspec.yml` | CodeBuild Docker build + ECR push spec |

## Resources Created

| Resource | Description |
|---|---|
| `aws_apprunner_service` | API container hosting (scale-to-zero) |
| `aws_dynamodb_table` x3 | CampaignSessions, AuditLogs, AgentRegistry |
| `aws_s3_bucket` x2 | Artifacts + CI/CD pipeline artifacts |
| `aws_kms_key` | Encryption at rest for all resources |
| `aws_iam_role` x5 | Red Agent, Blue Agent, Coordinator, Bedrock KB, CodeBuild |
| `aws_ecr_repository` | Docker image registry |
| `aws_bedrockagent_knowledge_base` | RAG knowledge base |
| `aws_opensearchserverless_collection` | Vector store for RAG |
| `aws_wafv2_web_acl` | WAF with managed rules + rate limiting |
| `aws_codepipeline` | CI/CD pipeline (GitHub → ECR → App Runner) |
| `aws_codebuild_project` | Docker build project |
| `aws_cloudwatch_event_rule` x2 | WAF anomaly + CloudWatch alarm triggers |
| `aws_sns_topic` | Blue Agent trigger notification |
| `aws_cloudwatch_log_group` x2 | App Runner + WAF logs |

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
aws s3 mb s3://purpleops-terraform-state --region us-east-1
aws dynamodb create-table \
  --table-name purpleops-tf-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

## Destroy

```bash
terraform destroy -var-file="terraform.tfvars"
```
