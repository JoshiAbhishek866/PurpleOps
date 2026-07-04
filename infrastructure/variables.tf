###############################################################################
# PurpleOps - Terraform Variables
###############################################################################

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "ecr_image_uri" {
  description = "ECR image URI override. Leave empty to use the ECR repo created by this config."
  type        = string
  default     = ""
  # If empty, main.tf uses: aws_ecr_repository.purpleops.repository_url + ":latest"
}

variable "bedrock_model_id" {
  description = "Amazon Bedrock model ID for agents"
  type        = string
  default     = "anthropic.claude-3-5-sonnet-20241022-v2:0"
}

variable "app_runner_cpu" {
  description = "App Runner CPU allocation"
  type        = string
  default     = "1 vCPU"

  validation {
    condition     = contains(["0.25 vCPU", "0.5 vCPU", "1 vCPU", "2 vCPU", "4 vCPU"], var.app_runner_cpu)
    error_message = "Invalid App Runner CPU value."
  }
}

variable "app_runner_memory" {
  description = "App Runner memory allocation"
  type        = string
  default     = "2 GB"

  validation {
    condition     = contains(["0.5 GB", "1 GB", "2 GB", "3 GB", "4 GB", "6 GB", "8 GB", "10 GB", "12 GB"], var.app_runner_memory)
    error_message = "Invalid App Runner memory value."
  }
}

variable "knowledge_base_id" {
  description = "Amazon Bedrock Knowledge Base ID for RAG"
  type        = string
  default     = ""
  sensitive   = true
}

variable "n8n_webhook_url" {
  description = "n8n webhook URL for workflow automation"
  type        = string
  default     = ""
  sensitive   = true
}

variable "enable_waf" {
  description = "Enable AWS WAF for the API"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365], var.log_retention_days)
    error_message = "Log retention must be a valid CloudWatch value."
  }
}

variable "tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}
