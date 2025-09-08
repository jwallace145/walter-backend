variable "name" {
  description = "Name of the IAM policy to create."
  type        = string
}

variable "description" {
  description = "Description for the IAM policy."
  type        = string
  default     = "Policy granting SQS consume permissions to specified queues."
}

variable "queue_arns" {
  description = "List of SQS queue ARNs this policy should allow consuming from."
  type        = list(string)

  validation {
    condition     = length(var.queue_arns) > 0
    error_message = "You must supply at least one SQS queue ARN."
  }
}

variable "tags" {
  description = "Tags to apply to the IAM policy."
  type        = map(string)
  default     = {}
}
