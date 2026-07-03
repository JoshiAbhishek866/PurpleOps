###############################################################################
# PurpleOps - CI/CD Pipeline
# CodePipeline: GitHub → CodeBuild (build + push ECR) → App Runner deploy
###############################################################################

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

# CodeBuild IAM role
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
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject", "s3:GetBucketVersioning"]
        Resource = [aws_s3_bucket.cicd_artifacts.arn, "${aws_s3_bucket.cicd_artifacts.arn}/*"]
      },
      {
        # Allow CodeBuild to trigger App Runner deployment after push
        Effect   = "Allow"
        Action   = ["apprunner:StartDeployment", "apprunner:DescribeService"]
        Resource = aws_apprunner_service.purpleops.arn
      }
    ]
  })
}

# CodeBuild project — buildspec is read from the repo root (buildspec.yml)
resource "aws_codebuild_project" "purpleops" {
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
    privileged_mode             = true
    image_pull_credentials_type = "CODEBUILD"

    environment_variable {
      name  = "ECR_REPO_URI"
      value = aws_ecr_repository.purpleops.repository_url
    }

    environment_variable {
      name  = "AWS_REGION"
      value = var.aws_region
    }

    environment_variable {
      name  = "AWS_ACCOUNT_ID"
      value = local.account_id
    }

    environment_variable {
      name  = "APP_RUNNER_SERVICE_ARN"
      value = aws_apprunner_service.purpleops.arn
    }
  }

  source {
    type      = "CODEPIPELINE"
    # buildspec.yml is read from the repo root automatically
  }

  logs_config {
    cloudwatch_logs {
      group_name  = aws_cloudwatch_log_group.purpleops.name
      stream_name = "codebuild"
    }
  }

  tags = { Name = "${local.name_prefix}-codebuild" }
}

# CodePipeline IAM role
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
        Action   = ["s3:GetObject", "s3:PutObject", "s3:GetBucketVersioning", "s3:GetObjectVersion"]
        Resource = [aws_s3_bucket.cicd_artifacts.arn, "${aws_s3_bucket.cicd_artifacts.arn}/*"]
      },
      {
        Effect   = "Allow"
        Action   = ["codebuild:BatchGetBuilds", "codebuild:StartBuild"]
        Resource = aws_codebuild_project.purpleops.arn
      },
      {
        Effect   = "Allow"
        Action   = ["codestar-connections:UseConnection"]
        Resource = aws_codestarconnections_connection.github.arn
      }
    ]
  })
}

# GitHub connection — requires one-time manual approval in AWS Console
resource "aws_codestarconnections_connection" "github" {
  name          = "${local.name_prefix}-github"
  provider_type = "GitHub"
}

# CodePipeline: Source → Build (build+push ECR + trigger App Runner)
# Note: App Runner has no native CodePipeline deploy action.
# The buildspec.yml handles the App Runner deployment via AWS CLI.
resource "aws_codepipeline" "purpleops" {
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
        ConnectionArn        = aws_codestarconnections_connection.github.arn
        FullRepositoryId     = "JoshiAbhishek866/Sentinal-AI"
        BranchName           = "main"
        DetectChanges        = "true"
        OutputArtifactFormat = "CODE_ZIP"
      }
    }
  }

  stage {
    name = "Build_and_Deploy"
    action {
      name             = "Build_Push_Deploy"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      version          = "1"
      input_artifacts  = ["source_output"]
      output_artifacts = ["build_output"]

      configuration = {
        ProjectName = aws_codebuild_project.purpleops.name
      }
    }
  }

  tags = { Name = "${local.name_prefix}-pipeline" }
}

output "codepipeline_name" {
  description = "CodePipeline name"
  value       = aws_codepipeline.purpleops.name
}

output "github_connection_arn" {
  description = "GitHub connection ARN — MUST be manually approved in AWS Console before pipeline runs"
  value       = aws_codestarconnections_connection.github.arn
}
