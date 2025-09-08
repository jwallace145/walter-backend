variable "service" {
  description = "The name of the service."
  type        = string

  default = "WalterBackend"
}

variable "name" {
  description = "The name of the queue."
  type        = string
}

variable "domain" {
  description = "The domain of WalterBackend."
  type        = string

  validation {
    condition     = contains(["dev", "stg", "prod"], var.domain)
    error_message = "Domain must be dev, stg, or prod!"
  }
}

variable "redrive_policy_max_receive_count" {
  description = "The maximum number of times a message will be delivered before being moved to the dead-letter queue."
  type        = number
  default     = 3
}