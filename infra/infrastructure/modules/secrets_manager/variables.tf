variable "secret_name" {
  description = "The name of the secret in AWS Secrets Manager"
  type        = string

  validation {
    condition     = can(regex("^[a-zA-Z0-9/_+=.@-]+$", var.secret_name))
    error_message = "Secret name can only contain alphanumeric characters and /_+=.@- symbols."
  }
}

variable "secret_description" {
  description = "Description of the secret"
  type        = string
  default     = ""
}

variable "secret_data" {
  description = "Map of key-value pairs to store as secret data"
  type        = map(string)
  sensitive   = true
}

variable "recovery_window_in_days" {
  description = "Number of days that AWS Secrets Manager waits before it can delete the secret"
  type        = number
  default     = 30
  validation {
    condition     = var.recovery_window_in_days >= 7 && var.recovery_window_in_days <= 30
    error_message = "Recovery window must be between 7 and 30 days."
  }
}

variable "kms_key_id" {
  description = "KMS Key ID to encrypt the secret. If not specified, uses the default KMS key"
  type        = string
  default     = null
}
