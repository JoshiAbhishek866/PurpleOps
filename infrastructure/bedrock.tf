###############################################################################
# Sentinel AI - Amazon Bedrock Resources
# Knowledge Base + Agent Registry (AgentCore)
###############################################################################

# OpenSearch Serverless collection for RAG vector store
resource "aws_opensearchserverless_collection" "knowledge_base" {
  name = "${local.name_prefix}-kb"
  type = "VECTORSEARCH"

  tags = {
    Name = "${local.name_prefix}-knowledge-base"
  }
}

# Encryption policy for OpenSearch
resource "aws_opensearchserverless_security_policy" "kb_encryption" {
  name = "${local.name_prefix}-kb-enc"
  type = "encryption"

  policy = jsonencode({
    Rules = [{
      ResourceType = "collection"
      Resource     = ["collection/${local.name_prefix}-kb"]
    }]
    AWSOwnedKey = true
  })
}

# Network policy — VPC access only
resource "aws_opensearchserverless_security_policy" "kb_network" {
  name = "${local.name_prefix}-kb-net"
  type = "network"

  policy = jsonencode([{
    Rules = [
      {
        ResourceType = "collection"
        Resource     = ["collection/${local.name_prefix}-kb"]
      },
      {
        ResourceType = "dashboard"
        Resource     = ["collection/${local.name_prefix}-kb"]
      }
    ]
    AllowFromPublic = true
  }])
}

# Data access policy — allow Bedrock service role
resource "aws_opensearchserverless_access_policy" "kb_data" {
  name = "${local.name_prefix}-kb-data"
  type = "data"

  policy = jsonencode([{
    Rules = [
      {
        ResourceType = "index"
        Resource     = ["index/${local.name_prefix}-kb/*"]
        Permission   = ["aoss:*"]
      },
      {
        ResourceType = "collection"
        Resource     = ["collection/${local.name_prefix}-kb"]
        Permission   = ["aoss:*"]
      }
    ]
    Principal = [
      aws_iam_role.bedrock_kb.arn,
      aws_iam_role.coordinator.arn
    ]
  }])
}

# IAM role for Bedrock Knowledge Base
resource "aws_iam_role" "bedrock_kb" {
  name = "${local.name_prefix}-bedrock-kb-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "bedrock.amazonaws.com" }
      Action    = "sts:AssumeRole"
      Condition = {
        StringEquals = {
          "aws:SourceAccount" = local.account_id
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "bedrock_kb" {
  name = "${local.name_prefix}-bedrock-kb-policy"
  role = aws_iam_role.bedrock_kb.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["aoss:APIAccessAll"]
        Resource = aws_opensearchserverless_collection.knowledge_base.arn
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:ListBucket"]
        Resource = [
          aws_s3_bucket.artifacts.arn,
          "${aws_s3_bucket.artifacts.arn}/*"
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["bedrock:InvokeModel"]
        Resource = "arn:aws:bedrock:${local.region}::foundation-model/amazon.titan-embed-text-v1"
      }
    ]
  })
}

# Bedrock Knowledge Base
resource "aws_bedrockagent_knowledge_base" "sentinel_ai" {
  name     = "${local.name_prefix}-knowledge-base"
  role_arn = aws_iam_role.bedrock_kb.arn

  knowledge_base_configuration {
    type = "VECTOR"
    vector_knowledge_base_configuration {
      embedding_model_arn = "arn:aws:bedrock:${local.region}::foundation-model/amazon.titan-embed-text-v1"
    }
  }

  storage_configuration {
    type = "OPENSEARCH_SERVERLESS"
    opensearch_serverless_configuration {
      collection_arn    = aws_opensearchserverless_collection.knowledge_base.arn
      vector_index_name = "sentinel-ai-index"
      field_mapping {
        vector_field   = "embedding"
        text_field     = "text"
        metadata_field = "metadata"
      }
    }
  }

  tags = {
    Name = "${local.name_prefix}-knowledge-base"
  }

  depends_on = [
    aws_opensearchserverless_access_policy.kb_data,
    aws_opensearchserverless_security_policy.kb_encryption,
    aws_opensearchserverless_security_policy.kb_network
  ]
}

# S3 data source for knowledge base (CVE docs, playbooks)
resource "aws_bedrockagent_data_source" "sentinel_ai" {
  knowledge_base_id = aws_bedrockagent_knowledge_base.sentinel_ai.id
  name              = "${local.name_prefix}-kb-datasource"

  data_source_configuration {
    type = "S3"
    s3_configuration {
      bucket_arn         = aws_s3_bucket.artifacts.arn
      inclusion_prefixes = ["knowledge-base/"]
    }
  }
}

output "knowledge_base_id" {
  description = "Bedrock Knowledge Base ID — set as KNOWLEDGE_BASE_ID env var"
  value       = aws_bedrockagent_knowledge_base.sentinel_ai.id
}
