variable "domain" {
  description = "The domain of WalterBackend."
  type        = string

  validation {
    condition     = contains(["dev", "stg", "prod"], var.domain)
    error_message = "The domain must be 'dev', 'stg', or 'prod'."
  }
}

variable "name" {
  description = "The name of the WalterBackend API to create the IAM role."
  type        = string
}

variable "description" {
  description = "The description of the WalterBackend API IAM role."
  type        = string
}

variable "secret_names" {
  description = "The names of the secret(s) the API requires access to for executions."
  type        = list(string)
}

variable "read_table_access_arns" {
  description = "The ARN(s) of the WalterDB DynamoDB tables that the API requires read access to items."
  type        = list(string)
}

variable "write_table_access_arns" {
  description = "The ARN(s) of the WalterDB DynamoDB tables that the API requires write access to items."
  type        = list(string)
}

variable "delete_table_access_arns" {
  description = "The ARNs of the WalterDB DynamoDB tables that the API requires delete access to items."
  type        = list(string)
}

variable "send_message_access_queue_arns" {
  description = "The ARN(s) of the SQS queues that the API requires permissions to send messages."
  type        = list(string)
}

variable "api_base_role" {
  description = "The IAM role used by the WalterBackend API function to assume the more specific API roles after routing."
  type        = string
}

variable "assume_api_role_principals" {
  description = "The principals other than the WalterBackend API function that are able to assume the API role. This is useful for enabling local API testing."
  type        = list(string)
}
