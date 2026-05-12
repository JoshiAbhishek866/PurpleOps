###############################################################################
# Sentinel AI - CI/CD Pipeline
# CodePipeline: GitHub → CodeBuild → ECR → App Runner
###############################################################################

# CodeBuild role
resource "aws_iam_role" "codebuild" {
  name = "${local.name_prefix}-codebuild-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "codebuild.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "codebuild" {
  name = "${local.name_prefix}-codebuild-policy"
  role = aws_iam_role.codebuild.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject"]
        Resource = "${aws_s3_bucket.cicd_artifacts.arn}/*"
      }
    ]
  })
}

# S3 bucket for pipeline artifacts
resource "aws_s3_bucket" "cicd_artifacts" {
  bucket = "${local.name_prefix}-cicd-${local.account_id}"
}

resource "aws_s3_bucket_public_access_block" "cicd_artifacts" {
  bucket                  = aws_s3_bucket.cicd_artifacts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# CodeBuild project — builds Docker image and pushes to ECR
resource "aws_codebuild_project" "sentinel_ai" {
  name          = "${local.name_prefix}-build"
  service_role  = aws_iam_role.codebuild.arn
  build_timeout = 20

  artifacts {
    type = "CODEPIPELINE"
  }

  environment {
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                       = "aws/codebuild/standard:7.0"
    type                        = "LINUX_CONTAINER"
    privileged_mode             = true  # Required for Docker builds
    image_pull_credentials_type = "CODEBUILD"

    environment_variable {
      name  = "ECR_REPO_URI"
      value = aws_ecr_repository.sentinel_ai.repository_url
    }

    environment_variable {
      name  = "AWS_REGION"
      value = var.aws_region
    }

    environment_variable {
      name  = "AWS_ACCOUNT_ID"
      value = local.account_id
    }
  }

  source {
    type      = "CODEPIPELINE"
    buildspec = file("${path.module}/buildspec.yml")
  }

  logs_config {
    cloudwatch_logs {
      group_name  = aws_cloudwatch_log_group.sentinel_ai.name
      stream_name = "codebuild"
    }
  }

  tags = {
    Name = "${local.name_prefix}-codebuild"
  }
}

# CodePipeline role
resource "aws_iam_role" "codepipeline" {
  name = "${local.name_prefix}-codepipeline-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "codepipeline.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "codepipeline" {
  name = "${local.name_prefix}-codepipeline-policy"
  role = aws_iam_role.codepipeline.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:*"]
        Resource = [aws_s3_bucket.cicd_artifacts.arn, "${aws_s3_bucket.cicd_artifacts.arn}/*"]
      },
      {
        Effect   = "Allow"
        Action   = ["codebuild:BatchGetBuilds", "codebuild:StartBuild"]
        Resource = aws_codebuild_project.sentinel_ai.arn
      },
      {
        Effect   = "Allow"
        Action   = ["codestar-connections:UseConnection"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["apprunner:StartDeployment"]
        Resource = aws_apprunner_service.sentinel_ai.arn
      }
    ]
  })
}

# GitHub connection (requires manual approval in AWS Console after apply)
resource "aws_codestarconnections_connection" "github" {
  name          = "${local.name_prefix}-github"
  provider_type = "GitHub"
}

# CodePipeline: GitHub → Build → Deploy
resource "aws_codepipeline" "sentinel_ai" {
  name     = "${local.name_prefix}-pipeline"
  role_arn = aws_iam_role.codepipeline.arn

  artifact_store {
    location = aws_s3_bucket.cicd_artifacts.bucket
    type     = "S3"
  }

  stage {
    name = "Source"
    action {
      name             = "GitHub_Source"
      category         = "Source"
      owner            = "AWS"
      provider         = "CodeStarSourceConnection"
      version          = "1"
      output_artifacts = ["source_output"]

      configuration = {
        ConnectionArn    = aws_codestarconnections_connection.github.arn
        FullRepositoryId = "JoshiAbhishek866/Sentinal-AI"
        BranchName       = "main"
        DetectChanges    = "true"
      }
    }
  }

  stage {
    name = "Build"
    action {
      name             = "Build_and_Push_ECR"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      version          = "1"
      input_artifacts  = ["source_output"]
      output_artifacts = ["build_output"]

      configuration = {
        ProjectName = aws_codebuild_project.sentinel_ai.name
      }
    }
  }

  stage {
    name = "Deploy"
    action {
      name            = "Deploy_AppRunner"
      category        = "Deploy"
      owner           = "AWS"
      provider        = "AppRunner"
      version         = "1"
      input_artifacts = ["build_output"]

      configuration = {
        ServiceArn = aws_apprunner_service.sentinel_ai.arn
      }
    }
  }

  tags = {
    Name = "${local.name_prefix}-pipeline"
  }
}

output "codepipeline_name" {
  description = "CodePipeline name"
  value       = aws_codepipeline.sentinel_ai.name
}

output "github_connection_arn" {
  description = "GitHub CodeStar connection — MUST be manually approved in AWS Console"
  value       = aws_codestarconnections_connection.github.arn
}
