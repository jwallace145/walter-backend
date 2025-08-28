output "id" {
  description = "The IAM role ID."
  value       = aws_iam_role.this.id
}

output "arn" {
  description = "The IAM role ARN."
  value       = aws_iam_role.this.arn
}

output "name" {
  description = "The IAM role name."
  value       = aws_iam_role.this.name
}
