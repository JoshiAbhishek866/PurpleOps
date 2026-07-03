###############################################################################
# PurpleOps - EventBridge
# Triggers Blue Agent within 5 seconds of WAF anomaly detection (FR-004)
###############################################################################

# EventBridge rule — fires on WAF blocked requests
resource "aws_cloudwatch_event_rule" "waf_anomaly" {
  name        = "${local.name_prefix}-waf-anomaly"
  description = "Trigger Blue Agent when WAF detects attack (FR-004: 5s response)"

  event_pattern = jsonencode({
    source      = ["aws.wafv2"]
    detail-type = ["AWS WAF Block"]
    detail = {
      action = ["BLOCK"]
    }
  })

  tags = {
    Name = "${local.name_prefix}-waf-anomaly-rule"
  }
}

# EventBridge rule — fires on CloudWatch alarm (high error rate)
resource "aws_cloudwatch_event_rule" "cloudwatch_alarm" {
  name        = "${local.name_prefix}-cw-alarm"
  description = "Trigger Blue Agent on CloudWatch anomaly alarm"

  event_pattern = jsonencode({
    source      = ["aws.cloudwatch"]
    detail-type = ["CloudWatch Alarm State Change"]
    detail = {
      state = { value = ["ALARM"] }
    }
  })
}

# SNS topic for Blue Agent notifications
resource "aws_sns_topic" "blue_agent_trigger" {
  name              = "${local.name_prefix}-blue-agent-trigger"
  kms_master_key_id = aws_kms_key.purpleops.arn  # Fixed: use .arn not .id

  tags = {
    Name = "${local.name_prefix}-blue-agent-trigger"
  }
}

# EventBridge → SNS for WAF anomaly
resource "aws_cloudwatch_event_target" "waf_to_sns" {
  rule      = aws_cloudwatch_event_rule.waf_anomaly.name
  target_id = "SendToSNS"
  arn       = aws_sns_topic.blue_agent_trigger.arn
}

# EventBridge → SNS for CloudWatch alarm
resource "aws_cloudwatch_event_target" "cw_to_sns" {
  rule      = aws_cloudwatch_event_rule.cloudwatch_alarm.name
  target_id = "SendToSNS"
  arn       = aws_sns_topic.blue_agent_trigger.arn
}

# SNS policy — allow EventBridge to publish
resource "aws_sns_topic_policy" "blue_agent_trigger" {
  arn = aws_sns_topic.blue_agent_trigger.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "events.amazonaws.com" }
      Action    = "SNS:Publish"
      Resource  = aws_sns_topic.blue_agent_trigger.arn
    }]
  })
}

output "blue_agent_trigger_topic_arn" {
  description = "SNS topic ARN that triggers Blue Agent"
  value       = aws_sns_topic.blue_agent_trigger.arn
}
