# Sentinel AI Architecture

## System Overview

Sentinel AI is an autonomous purple teaming platform built on AWS serverless architecture.

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend Layer                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Vue.js Dashboard (AWS Amplify)                      │   │
│  │  - Campaign Management                               │   │
│  │  - Real-time Monitoring                              │   │
│  │  - Compliance Reports                                │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Compute Layer                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  AWS App Runner (Python FastAPI)                     │   │
│  │  ┌────────────────┐      ┌────────────────┐         │   │
│  │  │  Red Agent     │      │  Blue Agent    │         │   │
│  │  │  (Offensive)   │      │  (Defensive)   │         │   │
│  │  └────────────────┘      └────────────────┘         │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  AI Intelligence Layer                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Amazon Bedrock (Claude 3.5 Sonnet)                  │   │
│  │  Knowledge Bases for Amazon Bedrock (RAG)            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  DynamoDB        │  │  S3              │                │
│  │  - Sessions      │  │  - Reports       │                │
│  │  - Audit Logs    │  │  - Artifacts     │                │
│  └──────────────────┘  └──────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

1. Admin initiates campaign via dashboard
2. Red Agent analyzes target and executes attacks
3. WAF/CloudWatch detects anomalies
4. Blue Agent triggered automatically
5. Blue Agent queries knowledge base
6. Blue Agent applies remediation
7. Compliance report generated
8. Knowledge base updated

## Security Model

- Red Agent: Read-only access, isolated IAM role
- Blue Agent: Write access to security controls only
- All actions logged to immutable audit trail
- KMS encryption for data at rest
- TLS 1.3 for data in transit

## Cost Optimization

- Scale-to-zero when idle
- Bedrock response caching
- On-demand DynamoDB pricing
- S3 lifecycle policies

## Deployment

- Docker container on AWS App Runner
- Infrastructure as Code (AWS CDK)
- CI/CD via AWS CodePipeline
- Multi-environment support (dev, staging, prod)
