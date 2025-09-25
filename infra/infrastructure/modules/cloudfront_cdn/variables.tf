variable "domain" {
  description = "The domain of WalterBackend."
  type        = string

  validation {
    condition     = contains(["dev", "stg", "prod"], var.domain)
    error_message = "The domain must be 'dev', 'stg', or 'prod'."
  }
}

variable "bucket_regional_domain_name" {
  description = ""
  type        = string
}

variable "origin_access_control_id" {
  description = "The ID of the OAC for CloudFront to access the S3 content."
  type        = string
}