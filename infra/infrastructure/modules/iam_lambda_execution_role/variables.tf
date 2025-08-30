variable "name" {
  description = "Name of the IAM role to create."
  type        = string
}

variable "description" {
  description = "Description of the IAM role."
  type        = string
}

variable "policies" {
  description = "List of managed policies with additional permissions to attach to the role."
  type        = map(string)
}
