output "role_arn" {
  value       = aws_iam_role.canary_role.arn
  description = "The IAM role ARN of the Canary role."
}

