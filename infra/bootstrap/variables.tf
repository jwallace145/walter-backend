variable "domain" {
  description = "The domain of WalterBackend."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "preprod", "prod"], var.domain)
    error_message = "Domain must be dev, preprod, or prod!"
  }
}
