/***************************
 * WalterBackend Variables *
 ***************************/

variable "domain" {
  description = "The domain of WalterBackend."
  type        = string

  validation {
    condition     = contains(["dev", "stg", "prod"], var.domain)
    error_message = "Domain must be dev, stg, or prod!"
  }
}

variable "log_level" {
  description = "The logging level of WalterBackend."
  type        = string

  validation {
    condition     = contains(["DEBUG", "INFO"], var.log_level)
    error_message = "log_level must be DEBUG or INFO!"
  }
}

variable "image_uri" {
  description = "The ECR image URI of WalterBackend."
  type        = string
}

variable "api_timeout_seconds" {
  description = "The timeout in seconds of all API endpoints."
  type        = number

  validation {
    condition     = var.api_timeout_seconds >= 0 && var.api_timeout_seconds <= 900
    error_message = "api_timeout_seconds must be between 0 and 900 seconds (15 minutes)!"
  }
}

variable "api_lambda_memory_mb" {
  description = "The memory in Megabytes (MB) allocated to the Lambda environments that serve the API endpoints."
  type        = number

  validation {
    condition     = var.api_lambda_memory_mb >= 0 && var.api_lambda_memory_mb <= 10240
    error_message = "api_lambda_memory_mb must be between 0 and 10240 MB!"
  }
}

variable "canary_timeout_seconds" {
  description = "The timeout in seconds of all API canaries."
  type        = number

  validation {
    condition     = var.canary_timeout_seconds >= 0 && var.canary_timeout_seconds <= 900
    error_message = "canary_timeout_seconds must be between 0 and 900 seconds (15 minutes)!"
  }
}

variable "canary_lambda_memory_mb" {
  description = "The memory in Megabytes (MB) allocated to the Lambda environments that serve the API canaries."
  type        = number

  validation {
    condition     = var.canary_lambda_memory_mb >= 0 && var.canary_lambda_memory_mb <= 10240
    error_message = "canary_lambda_memory_mb must be between 0 and 10240 MB!"
  }
}

variable "workflow_timeout_seconds" {
  description = "The timeout in seconds of all asynchronous workflows."
  type        = number
  default     = 180

  validation {
    condition     = var.workflow_timeout_seconds >= 0 && var.workflow_timeout_seconds <= 900
    error_message = "workflow_timeout_seconds must be between 0 and 900 seconds (15 minutes)!"
  }
}

variable "workflow_lambda_memory_mb" {
  description = "The memory in Megabytes (MB) allocated to the Lambda environments that serve the workflows."
  type        = number
  default     = 1024

  validation {
    condition     = var.workflow_lambda_memory_mb >= 0 && var.workflow_lambda_memory_mb <= 10240
    error_message = "workflow_lambda_memory_mb must be between 0 and 10240 MB!"
  }
}
