variable "domain" {
  description = "The domain of WalterBackend."
  type        = string

  validation {
    condition     = contains(["dev", "stg", "prod"], var.domain)
    error_message = "The domain must be 'dev', 'stg', or 'prod'."
  }
}

variable "name" {
  description = "The name of the WalterBackend Canary to create the IAM role."
  type        = string
}

variable "description" {
  description = "The description of the WalterBackend Canary IAM role."
  type        = string
}

variable "secret_names" {
  description = "The names of the secret(s) the canary requires access to for executions."
  type        = list(string)
}

variable "read_table_access_arns" {
  description = "The ARN(s) of the WalterDB DynamoDB tables that the canary requires read access to items."
  type        = list(string)
}

variable "write_table_access_arns" {
  description = "The ARN(s) of the WalterDB DynamoDB tables that the canary requires write access to items."
  type        = list(string)
}

variable "delete_table_access_arns" {
  description = "The ARNs of the WalterDB DynamoDB tables that the canary requires delete access to items."
  type        = list(string)
}

variable "canary_base_role" {
  description = "The IAM role used by the WalterBackend API function to assume the more specific canary roles after routing."
  type        = string
}

variable "assume_canary_role_principals" {
  description = "The principals other than the WalterBackend Canary function that are able to assume the Canary role(s). This is useful for enabling local Canary testing."
  type        = list(string)
}
