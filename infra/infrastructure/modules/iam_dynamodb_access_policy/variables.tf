variable "table_names" {
  description = "List of DynamoDB table names to grant access to."
  type        = list(string)
}

variable "policy_name" {
  description = "Optional name for the IAM policy. If not provided, a default name will be used."
  type        = string
}