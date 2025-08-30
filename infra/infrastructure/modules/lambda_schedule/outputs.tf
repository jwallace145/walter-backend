output "rule_name" {
  description = "Name of the created EventBridge rule."
  value       = aws_cloudwatch_event_rule.this.name
}

output "rule_arn" {
  description = "ARN of the created EventBridge rule."
  value       = aws_cloudwatch_event_rule.this.arn
}
