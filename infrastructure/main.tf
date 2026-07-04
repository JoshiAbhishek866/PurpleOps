###############################################################################
# PurpleOps - Main Terraform Configuration
###############################################################################

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.31"  # 5.31+ required for aws_bedrockagent_* resources
    }
  }

  # Remote state — create the bucket + lock table first (see bootstrap/README.md)
  backend "s3" {
    bucket         = "purpleops-terraform-state"
    key            = "purpleops/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "purpleops-tf-lock"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "purpleops"
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = "abhishek-joshi"
    }
  }
}

###############################################################################
# Data Sources
###############################################################################

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  account_id  = data.aws_caller_identity.current.account_id
  region      = data.aws_region.current.name
  name_prefix = "purpleops-${var.environment}"

  # ECR image URI: use override var if provided, else use the ECR repo created here
  ecr_image_uri = var.ecr_image_uri != "" ? var.ecr_image_uri : "${aws_ecr_repository.purpleops.repository_url}:latest"
}

###############################################################################
# DynamoDB Tables
###############################################################################

resource "aws_dynamodb_table" "campaign_sessions" {
  name         = "${local.name_prefix}-campaign-sessions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "campaign_id"
  range_key    = "timestamp"

  attribute {
    name = "campaign_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.purpleops.arn
  }

  tags = { Name = "CampaignSessions" }
}

resource "aws_dynamodb_table" "audit_logs" {
  name         = "${local.name_prefix}-audit-logs"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "session_id"
  range_key    = "event_timestamp"

  attribute {
    name = "session_id"
    type = "S"
  }

  attribute {
    name = "event_timestamp"
    type = "N"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.purpleops.arn
  }

  tags = { Name = "AuditLogs" }
}

resource "aws_dynamodb_table" "agent_registry" {
  name         = "${local.name_prefix}-agent-registry"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "agent_id"
  range_key    = "version"

  attribute {
    name = "agent_id"
    type = "S"
  }

  attribute {
    name = "version"
    type = "S"
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.purpleops.arn
  }

  tags = { Name = "SentinelAgentRegistry" }
}

###############################################################################
# S3 Bucket — Artifacts & Reports
###############################################################################

resource "aws_s3_bucket" "artifacts" {
  bucket = "${local.name_prefix}-artifacts-${local.account_id}"
}

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.purpleops.arn
    }
  }
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket                  = aws_s3_bucket.artifacts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    id     = "archive-old-reports"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 365
    }
  }
}

###############################################################################
# KMS Key — Encryption at Rest
###############################################################################

resource "aws_kms_key" "purpleops" {
  description             = "PurpleOps encryption key"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = { Name = "${local.name_prefix}-kms" }
}

resource "aws_kms_alias" "purpleops" {
  name          = "alias/${local.name_prefix}"
  target_key_id = aws_kms_key.purpleops.key_id
}

###############################################################################
# IAM — App Runner instance role (used by the running container)
###############################################################################

resource "aws_iam_role" "apprunner_instance" {
  name = "${local.name_prefix}-apprunner-instance-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "tasks.apprunner.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "apprunner_instance" {
  name = "${local.name_prefix}-apprunner-instance-policy"
  role = aws_iam_role.apprunner_instance.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem", "dynamodb:GetItem",
          "dynamodb:UpdateItem", "dynamodb:Query", "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.campaign_sessions.arn,
          aws_dynamodb_table.audit_logs.arn,
          aws_dynamodb_table.agent_registry.arn
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["bedrock:InvokeModel", "bedrock:RetrieveAndGenerate", "bedrock:Retrieve"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject", "s3:GetObject"]
        Resource = "${aws_s3_bucket.artifacts.arn}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["wafv2:UpdateWebACL", "wafv2:GetWebACL", "wafv2:ListWebACLs"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["bedrock:CreateAgent", "bedrock:GetAgent", "bedrock:ListAgents"]
        Resource = "*"
      }
    ]
  })
}

# IAM — App Runner access role (pulls image from ECR)
resource "aws_iam_role" "apprunner_access" {
  name = "${local.name_prefix}-apprunner-access-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "build.apprunner.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "apprunner_ecr" {
  role       = aws_iam_role.apprunner_access.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

###############################################################################
# IAM — Separate roles for Red/Blue/Coordinator (for future STS assume)
###############################################################################

resource "aws_iam_role" "red_agent" {
  name = "${local.name_prefix}-red-agent-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { AWS = aws_iam_role.apprunner_instance.arn }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "red_agent" {
  name = "${local.name_prefix}-red-agent-policy"
  role = aws_iam_role.red_agent.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ec2:Describe*", "wafv2:Get*", "wafv2:List*"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["dynamodb:PutItem"]
        Resource = aws_dynamodb_table.audit_logs.arn
      },
      {
        Effect   = "Deny"
        Action   = ["wafv2:UpdateWebACL", "ec2:Modify*", "iam:*", "s3:Delete*"]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role" "blue_agent" {
  name = "${local.name_prefix}-blue-agent-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { AWS = aws_iam_role.apprunner_instance.arn }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "blue_agent" {
  name = "${local.name_prefix}-blue-agent-policy"
  role = aws_iam_role.blue_agent.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "wafv2:UpdateWebACL", "wafv2:CreateWebACL",
        "ec2:ModifySecurityGroupRules",
        "dynamodb:PutItem",
        "s3:PutObject",
        "bedrock:InvokeModel", "bedrock:RetrieveAndGenerate"
      ]
      Resource = "*"
    }]
  })
}

resource "aws_iam_role" "coordinator" {
  name = "${local.name_prefix}-coordinator-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { AWS = aws_iam_role.apprunner_instance.arn }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "coordinator" {
  name = "${local.name_prefix}-coordinator-policy"
  role = aws_iam_role.coordinator.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem", "dynamodb:GetItem",
          "dynamodb:UpdateItem", "dynamodb:Query", "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.campaign_sessions.arn,
          aws_dynamodb_table.audit_logs.arn,
          aws_dynamodb_table.agent_registry.arn
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["bedrock:InvokeModel", "bedrock:CreateAgent", "bedrock:GetAgent"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject", "s3:GetObject"]
        Resource = "${aws_s3_bucket.artifacts.arn}/*"
      }
    ]
  })
}

###############################################################################
# App Runner — API Service
###############################################################################

resource "aws_apprunner_service" "purpleops" {
  service_name = "${local.name_prefix}-api"

  source_configuration {
    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_access.arn
    }

    image_repository {
      image_identifier      = local.ecr_image_uri
      image_repository_type = "ECR"

      image_configuration {
        port = "8000"
        runtime_environment_variables = {
          AWS_REGION               = var.aws_region
          BEDROCK_MODEL_ID         = var.bedrock_model_id
          DYNAMODB_TABLE_CAMPAIGNS = aws_dynamodb_table.campaign_sessions.name
          DYNAMODB_TABLE_AUDIT     = aws_dynamodb_table.audit_logs.name
          S3_BUCKET_REPORTS        = aws_s3_bucket.artifacts.bucket
          AGENT_REGISTRY_TABLE     = aws_dynamodb_table.agent_registry.name
          RED_AGENT_ROLE_ARN       = aws_iam_role.red_agent.arn
          BLUE_AGENT_ROLE_ARN      = aws_iam_role.blue_agent.arn
          COORD_AGENT_ROLE_ARN     = aws_iam_role.coordinator.arn
          DEFAULT_MAX_ATTACK_TURNS = "5"
          DEFAULT_MAX_DEFENSE_TURNS = "5"
          DEFAULT_TOKEN_BUDGET     = "50000"
          AGENT_MODE               = "default"
        }
      }
    }
    auto_deployments_enabled = false  # CI/CD pipeline handles deployments
  }

  instance_configuration {
    cpu               = var.app_runner_cpu
    memory            = var.app_runner_memory
    instance_role_arn = aws_iam_role.apprunner_instance.arn
  }

  health_check_configuration {
    protocol            = "HTTP"
    path                = "/health"
    interval            = 10
    timeout             = 5
    healthy_threshold   = 1
    unhealthy_threshold = 5
  }

  tags = { Name = "${local.name_prefix}-api" }
}

###############################################################################
# CloudWatch — Log Group & Alarms
###############################################################################

resource "aws_cloudwatch_log_group" "purpleops" {
  name              = "/aws/apprunner/${local.name_prefix}"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_metric_alarm" "high_token_usage" {
  alarm_name          = "${local.name_prefix}-high-token-usage"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "TokensUsed"
  namespace           = "PurpleOps"
  period              = 3600
  statistic           = "Sum"
  threshold           = 40000
  alarm_description   = "Token usage approaching budget limit"
  alarm_actions       = []
}
