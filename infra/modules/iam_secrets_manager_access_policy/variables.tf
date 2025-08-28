

variable "secret_names" {
  description = "List of Secrets Manager secret names to grant access to (without the random suffix)."
  type        = list(string)
}

variable "policy_name" {
  description = "Name for the IAM policy to be created."
  type        = string
}
