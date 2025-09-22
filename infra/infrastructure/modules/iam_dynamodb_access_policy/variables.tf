variable "policy_name" {
  description = "Optional name for the IAM policy. If not provided, a default name will be used."
  type        = string
}

variable "read_access_table_arns" {
  description = "List of DynamoDB table ARNs to grant READ access to. Index ARNs will be derived automatically."
  type        = list(string)
}

variable "write_access_table_arns" {
  description = "List of DynamoDB table ARNs to grant WRITE access to."
  type        = list(string)
}

variable "delete_access_table_arns" {
  description = "List of DynamoDB table ARNs to grant DELETE access to."
  type        = list(string)
}