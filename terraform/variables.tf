variable "domain" {
  description = "The domain of WalterBackend."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "preprod", "prod"], var.domain)
    error_message = "Domain must be dev, preprod, or prod!"
  }
}

variable "log_level" {
  description = "The logging level of WalterBackend."
  type        = string
  default     = "INFO"

  validation {
    condition     = contains(["DEBUG", "INFO"], var.log_level)
    error_message = "log_level must be DEBUG or INFO!"
  }
}

variable "image_uri" {
  description = "The ECR image URI of WalterBackend."
  type        = string
  default     = "010526272437.dkr.ecr.us-east-1.amazonaws.com/walter/api:latest"
}

variable "api_timeout_seconds" {
  description = "The timeout in seconds of all API endpoints."
  type        = number
  default     = 15
}

variable "api_lambda_memory_mb" {
  description = "The memory in Megabytes (MB) allocated to the Lambda environments that serve the API endpoints."
  type        = number
  default     = 256
}

variable "workflow_timeout_seconds" {
  description = "The timeout in seconds of all asynchronous workflows."
  type        = number
  default     = 180
}

variable "workflow_lambda_memory_mb" {
  description = "The memory in Megabytes (MB) allocated to the Lambda environments that serve the workflows."
  type        = number
  default     = 512
}

variable "canary_timeout_seconds" {
  description = "The timeout in seconds of all API canaries."
  type        = number
  default     = 15
}

variable "canary_lambda_memory_mb" {
  description = "The memory in Megabytes (MB) allocated to the Lambda environments that serve the API canaries."
  type        = number
  default     = 128
}