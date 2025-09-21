variable "domain" {
  description = "The domain of WalterBackend."
  type        = string

  validation {
    condition     = contains(["dev", "stg", "prod"], var.domain)
    error_message = "The domain must be 'dev', 'stg', or 'prod'."
  }
}

variable "name" {
  description = "The name of the VPC."
  type        = string
}

variable "vpc_cidr" {
  description = "The CIDR block of the VPC."
  type        = string
}

variable "public_subnet_cidr" {
  description = "The CIDR block of the public subnet."
  type        = string
}

variable "private_subnet_cidr" {
  description = "The CIDR block of the private subnet."
  type        = string
}

variable "availability_zone" {
  description = "The availability zone to use."
  type        = string

  validation {
    condition     = startswith(var.availability_zone, data.aws_region.current.name)
    error_message = "The availability_zone must start with the current AWS region (e.g., us-east-1a if region is us-east-1)."
  }
}

# Look up the current region from AWS credentials / provider
data "aws_region" "current" {}
