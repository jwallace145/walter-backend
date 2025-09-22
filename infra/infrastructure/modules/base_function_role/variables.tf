variable "account_id" {
  type = string
}

variable "domain" {
  description = "The domain of WalterBackend."
  type        = string

  validation {
    condition     = contains(["dev", "stg", "prod"], var.domain)
    error_message = "The domain must be 'dev', 'stg', or 'prod'."
  }
}

variable "component" {
  type = string
}

variable "description" {
  type = string
}

variable "assumable_entities" {
  type = list(string)
}

variable "kms_key_arns" {
  type = list(string)
}

variable "receive_message_queue_access_arns" {
  description = "The list of SQS queue ARN(s) that the workflow requires receive message access."
  type        = list(string)
  default     = []
}


