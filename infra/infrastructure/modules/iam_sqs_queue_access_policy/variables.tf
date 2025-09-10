variable "name" {
  description = "Name of the IAM policy to create."
  type        = string
}

variable "description" {
  description = "Description for the IAM policy."
  type        = string
  default     = "Policy granting SQS access to specified queues."
}

variable "access_type" {
  description = "Type of access this policy grants to the queues. One of: \"consumer\" or \"producer\"."
  type        = string
  default     = "consumer"

  validation {
    condition     = contains(["consumer", "producer"], var.access_type)
    error_message = "access_type must be either 'consumer' or 'producer'."
  }
}

variable "queue_arns" {
  description = "List of SQS queue ARNs this policy should apply to."
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
