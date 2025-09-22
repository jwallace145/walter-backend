variable "domain" {
  description = "The domain of WalterBackend."
  type        = string

  validation {
    condition     = contains(["dev", "stg", "prod"], var.domain)
    error_message = "The domain must be 'dev', 'stg', or 'prod'."
  }
}

variable "name" {
  description = "The name of the WalterBackend Workflow to create the IAM role."
  type        = string
}

variable "description" {
  description = "The description of the WalterBackend Workflow IAM role."
  type        = string
}

variable "secrets_access" {
  description = "The names of the secret(s) the workflow requires access to for executions."
  type        = list(string)
}

variable "read_table_access_arns" {
  description = "The ARN(s) of the WalterDB DynamoDB tables that the workflow requires read access to items."
  type        = list(string)
}

variable "write_table_access_arns" {
  description = "The ARN(s) of the WalterDB DynamoDB tables that the workflow requires write access to items."
  type        = list(string)
}

variable "delete_table_access_arns" {
  description = "The ARNs of the WalterDB DynamoDB tables that the workflow requires delete access to items."
  type        = list(string)
}

variable "receive_message_access_queue_arns" {
  description = "The ARN(s) of the SQS queues that the workflow can receive messages from for task processing."
  type        = list(string)
}

variable "workflow_base_role" {
  description = "The IAM role used by the WalterBackend workflow function to assume the more specific workflow roles after routing."
  type        = string
}

variable "additional_principals" {
  description = "The principals other than the WalterBackend workflow function that are able to assume the workflow role. This is useful for enabling local workflow testing."
  type        = list(string)
}

