###############################################################################
# Sentinel AI - ECR Repository
# Stores Docker images for the API container
###############################################################################

resource "aws_ecr_repository" "sentinel_ai" {
  name                 = "${local.name_prefix}-api"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.sentinel_ai.arn
  }

  tags = {
    Name = "${local.name_prefix}-ecr"
  }
}

resource "aws_ecr_lifecycle_policy" "sentinel_ai" {
  repository = aws_ecr_repository.sentinel_ai.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = { type = "expire" }
      }
    ]
  })
}

output "ecr_repository_url" {
  description = "ECR repository URL — use this as ecr_image_uri in tfvars"
  value       = "${aws_ecr_repository.sentinel_ai.repository_url}:latest"
}
