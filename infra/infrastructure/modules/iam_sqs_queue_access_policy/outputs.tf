output "policy_arn" {
  value       = aws_iam_policy.this.arn
  description = "The ARN of the created IAM policy."
}

output "policy_name" {
  value       = aws_iam_policy.this.name
  description = "The name of the created IAM policy."
}

output "policy_id" {
  value       = aws_iam_policy.this.id
  description = "The ID of the created IAM policy."
}

output "policy_document" {
  value       = data.aws_iam_policy_document.this.json
  description = "The JSON policy document."
}
