variable "domain" {
  description = "The domain of the API."
  type        = string

  validation {
    condition     = contains(["dev", "stg", "prod"], var.domain)
    error_message = "The domain must be 'dev', 'stg', or 'prod'."
  }
}

variable "base_domain" {
  description = "The base domain name of the API."
  type        = string
}

variable "hosted_zone_id" {
  description = "The Route 53 Hosted Zone ID for the base domain."
  type        = string
}

variable "api_id" {
  description = "The API Gateway REST API ID."
  type        = string
}

variable "stage_name" {
  description = "The API Gateway stage name."
  type        = string
}


