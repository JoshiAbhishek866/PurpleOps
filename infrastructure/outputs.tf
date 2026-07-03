###############################################################################
# PurpleOps - Terraform Outputs
###############################################################################

output "app_runner_service_url" {
  description = "PurpleOps API URL"
  value       = "https://${aws_apprunner_service.purpleops.service_url}"
}

output "app_runner_service_arn" {
  description = "App Runner service ARN"
  value       = aws_apprunner_service.purpleops.arn
}

output "dynamodb_campaigns_table" {
  description = "DynamoDB CampaignSessions table name"
  value       = aws_dynamodb_table.campaign_sessions.name
}

output "dynamodb_audit_table" {
  description = "DynamoDB AuditLogs table name"
  value       = aws_dynamodb_table.audit_logs.name
}

output "dynamodb_registry_table" {
  description = "DynamoDB AgentRegistry table name"
  value       = aws_dynamodb_table.agent_registry.name
}

output "s3_artifacts_bucket" {
  description = "S3 bucket for compliance reports and artifacts"
  value       = aws_s3_bucket.artifacts.bucket
}

output "kms_key_arn" {
  description = "KMS key ARN for encryption"
  value       = aws_kms_key.purpleops.arn
  sensitive   = true
}

output "red_agent_role_arn" {
  description = "IAM role ARN for Red Agent"
  value       = aws_iam_role.red_agent.arn
}

output "blue_agent_role_arn" {
  description = "IAM role ARN for Blue Agent"
  value       = aws_iam_role.blue_agent.arn
}

output "coordinator_role_arn" {
  description = "IAM role ARN for Coordinator Agent"
  value       = aws_iam_role.coordinator.arn
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.purpleops.name
}

output "account_id" {
  description = "AWS Account ID"
  value       = local.account_id
}

output "region" {
  description = "AWS Region"
  value       = local.region
}
