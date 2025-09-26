variable "domain" {
  description = "The domain of WalterBackend."
  type        = string

  validation {
    condition     = contains(["dev", "stg", "prod"], var.domain)
    error_message = "The domain must be 'dev', 'stg', or 'prod'."
  }
}

variable "name" {
  description = "The name of the API Gateway."
  type        = string
}

variable "description" {
  description = "The description of the API Gateway."
  type        = string
}

variable "function_name" {
  description = "The name of the Lambda function the API Gateway invokes."
  type        = string
}

variable "alias_name" {
  description = "The name of the alias used to increment versions of the Lambda function."
  type        = string
}

variable "image_digest" {
  description = "The image digest of the image used for the Lambda functions to trigger new API deployments."
  type        = string
}

variable "stage_name" {
  description = "The name of the stage to create for the API Gateway."
  type        = string
}

variable "log_retention_in_days" {
  description = "The number of days to retain API Gateway logs."
  type        = number
}

variable "api_key_value" {
  description = "The value of the API key used to restrict access to the API Gateway to known callers."
  type        = string
}

variable "rate_limit" {
  description = "The steady-state number of requests per second allowed to the API before throttling occurs."
  type        = number
}

variable "burst_limit" {
  description = "The maximum number of requests that the API can handle in a short burst before throttling."
  type        = number
}
