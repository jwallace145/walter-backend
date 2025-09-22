variable "account_id" {
  description = "The AWS account ID of the owner account of the KMS key."
  type        = string
}

variable "domain" {
  description = "The domain of WalterBackend."
  type        = string

  validation {
    condition     = contains(["dev", "stg", "prod"], var.domain)
    error_message = "The domain must be 'dev', 'stg', or 'prod'."
  }
}

variable "name" {
  description = "The name of the KMS key."
  type        = string
}

variable "description" {
  description = "The description of the KMS key."
  type        = string
}

variable "deletion_window_in_days" {
  description = "The number of days to wait before permanent deletion of KMS key after starting the deletion process."
  type        = number
  default     = 30
}