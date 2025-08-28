

output "policy_arn" {
  description = "ARN of the IAM policy that grants Secrets Manager access."
  value       = aws_iam_policy.this.arn
}

output "policy_id" {
  description = "IAM policy id."
  value       = aws_iam_policy.this.id
}

output "policy_name" {
  description = "Name of the IAM policy."
  value       = aws_iam_policy.this.name
}

output "policy_document_json" {
  description = "Rendered JSON of the IAM policy document."
  value       = data.aws_iam_policy_document.this.json
}
