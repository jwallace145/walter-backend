output "role_arn" {
  value       = aws_iam_role.workflow_role.arn
  description = "The IAM role ARN of the workflow role."
}

