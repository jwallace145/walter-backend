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

variable "timeout" {
  description = "The timeout of the Lambda function."
  type        = number
}