variable "function_name" {
  description = "Name of the Lambda function"
  type        = string
}

variable "description" {
  description = "Description of the Lambda function"
  type        = string
  default     = null
}

variable "image_uri" {
  description = "ECR image URI for the Lambda function"
  type        = string
}

variable "role_arn" {
  description = "IAM role ARN for the Lambda function"
  type        = string
}

variable "timeout" {
  description = "Timeout in seconds for the Lambda function"
  type        = number
}

variable "memory_size" {
  description = "Memory size in MB for the Lambda function"
  type        = number
}

variable "lambda_handler" {
  description = "The actual handler inside the container that Datadog should forward to"
  type        = string
}

variable "log_level" {
  description = "Log level for the function"
  type        = string
}

variable "domain" {
  description = "Deployment domain identifier"
  type        = string
}

variable "publish" {
  description = "Whether to publish a new version on updates"
  type        = bool
  default     = true
}

variable "log_retention_in_days" {
  description = "Lambda function log retention in days"
  type        = number
  default     = 7
}

variable "datadog_api_key" {
  description = "The Datadog API key used to emit metrics and forward logs to Datadog"
  type        = string
}

variable "datadog_site" {
  description = "The Datadog site used send application data to Datadog"
  type        = string
}

variable "provisioned_concurrent_executions" {
  description = "The number of concurrent executions to reserve for the function"
  type        = number
  default     = 1
}

variable "alias_name" {
  description = "Alias name for the Lambda function"
  type        = string
}
