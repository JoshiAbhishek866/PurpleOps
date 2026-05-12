###############################################################################
# Sentinel AI - Terraform Variable Values
# WARNING: Do NOT commit sensitive values. Use terraform.tfvars.local or
#          environment variables (TF_VAR_*) for secrets.
###############################################################################

aws_region   = "us-east-1"
environment  = "dev"

# Update this after building and pushing your Docker image to ECR
ecr_image_uri = "REPLACE_WITH_YOUR_ECR_IMAGE_URI"
# Example: 123456789012.dkr.ecr.us-east-1.amazonaws.com/sentinel-ai:latest

bedrock_model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"

app_runner_cpu    = "1 vCPU"
app_runner_memory = "2 GB"

enable_waf         = true
log_retention_days = 30

tags = {
  Project = "sentinel-ai"
  Team    = "security"
}

# Sensitive values — set via environment variables instead:
# export TF_VAR_knowledge_base_id="your-kb-id"
# export TF_VAR_n8n_webhook_url="http://your-n8n-instance/webhook"
