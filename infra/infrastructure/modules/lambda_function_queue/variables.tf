variable "function_name" {
  description = "Name of the Lambda function"
  type        = string
}

variable "queue_arn" {
  description = "ARN of the SQS queue"
  type        = string
}

variable "batch_size" {
  description = "Maximum number of messages to retrieve in a single batch"
  type        = number
  default     = 1
}

variable "maximum_batching_window_in_seconds" {
  description = "Maximum time to wait for additional messages before invoking the function"
  type        = number
  default     = 0
}

variable "enabled" {
  description = "Whether the event source mapping is enabled"
  type        = bool
  default     = true
}

variable "function_response_types" {
  description = "List of response types for the function"
  type        = list(string)
  default     = ["ReportBatchItemFailures"]
}

variable "maximum_concurrency" {
  description = "Maximum number of concurrent executions for the function"
  type        = number
  default     = 2
}