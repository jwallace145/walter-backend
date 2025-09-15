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

variable "table_names" {
  description = "The names of the WalterDB table(s) the API requires access to for executions."
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
