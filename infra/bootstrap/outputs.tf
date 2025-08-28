output "s3_bucket_name" {
  description = "Name of the S3 bucket for Terraform state"
  value       = aws_s3_bucket.terraform_state.bucket
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket for Terraform state"
  value       = aws_s3_bucket.terraform_state.arn
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table for state locking"
  value       = aws_dynamodb_table.terraform_locks.name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table for state locking"
  value       = aws_dynamodb_table.terraform_locks.arn
}

output "terraform_backend_config" {
  description = "Terraform backend configuration block"
  value       = <<-EOT
terraform {
  backend "s3" {
    bucket         = "${aws_s3_bucket.terraform_state.bucket}"
    key            = "terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "${aws_dynamodb_table.terraform_locks.name}"
    encrypt        = true
  }
}
EOT
}
