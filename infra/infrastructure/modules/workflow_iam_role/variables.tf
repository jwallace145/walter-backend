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

variable "tables_access" {
  description = "The names of the WalterDB table(s) the workflow requires access to for executions."
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

