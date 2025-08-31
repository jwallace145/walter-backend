variable "domain" {
  description = "The domain of WalterBackend."
  type        = string

  validation {
    condition     = contains(["dev", "stg", "prod"], var.domain)
    error_message = "Domain must be dev, stg, or prod!"
  }
}

variable "component_name" {
  description = "The name of the component."
  type        = string
}

variable "function_name" {
  description = "The name of the Lambda function."
  type        = string
}

variable "function_memory_mb" {
  description = "The maximum memory of the Lambda function."
  type        = number

  validation {
    condition     = var.function_memory_mb >= 0 && var.function_memory_mb <= 10240
    error_message = "Lambda function memory must be between 0 and 10240 MB!"
  }
}