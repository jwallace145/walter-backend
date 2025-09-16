output "function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.this.arn
}

output "function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.this.function_name
}

output "alias_name" {
  description = "The alias of the Lambda function."
  value       = aws_lambda_alias.release.name
}

output "invoke_arn" {
  description = "Invoke ARN of the Lambda function"
  value       = aws_lambda_alias.release.invoke_arn
}

output "id" {
  description = "ID of the Lambda function resource"
  value       = aws_lambda_function.this.id
}

output "kms_key_arn" {
  description = "The KMS key ARN used to encrypt/decrypt the Lambda function environment variables."
  value       = aws_kms_key.env_vars_kms_key.arn
}
