output "role_arn" {
  value       = aws_iam_role.api_iam_role.arn
  description = "The IAM role ARN of the API role."
}
