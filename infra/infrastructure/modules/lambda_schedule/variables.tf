

variable "name" {
  description = "Name of the EventBridge Rule."
  type        = string
}

variable "description" {
  description = "Description of the EventBridge Rule."
  type        = string
  default     = null
}

variable "schedule_expression" {
  description = "Schedule expression (rate(...) or cron(...))."
  type        = string
}

variable "lambda_function_arn" {
  description = "ARN of the Lambda function to invoke."
  type        = string
}

variable "input" {
  description = "JSON string passed as the input to the Lambda target. If null, no input is set."
  type        = string
  default     = null
}

variable "enabled" {
  description = "Whether the EventBridge rule is enabled."
  type        = bool
  default     = true
}

variable "target_id" {
  description = "Identifier for the target attached to the rule."
  type        = string
  default     = "lambda"
}
