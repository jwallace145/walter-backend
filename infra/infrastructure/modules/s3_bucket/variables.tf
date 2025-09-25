variable "domain" {
  description = "The domain of WalterBackend."
  type        = string

  validation {
    condition     = contains(["dev", "stg", "prod"], var.domain)
    error_message = "The domain must be 'dev', 'stg', or 'prod'."
  }
}

variable "name_prefix" {
  description = "The name prefix of the S3 bucket."
  type        = string
}

variable "read_access_principals" {
  description = "The AWS principal(s) that can read objects in the bucket scoped by prefix."
  type = list(object({
    prefix     = string
    principals = list(string)
  }))
  default = []

  validation {
    condition = alltrue([
      for item in var.read_access_principals :
      can(regex("^[a-zA-Z0-9!_.*'()-/]*$", item.prefix))
    ])
    error_message = "All prefix values must contain only valid S3 prefix characters."
  }

  validation {
    condition     = alltrue([for item in var.read_access_principals : (length(item.principals) > 0)])
    error_message = "Each principals list must contain at least one principal."
  }
}

variable "write_access_principals" {
  description = "The AWS principal(s) that can write and update objects in the bucket scoped by prefix."
  type = list(object({
    prefix     = string
    principals = list(string)
  }))
  default = []

  validation {
    condition = alltrue([
      for item in var.write_access_principals :
      can(regex("^[a-zA-Z0-9!_.*'()-/]*$", item.prefix))
    ])
    error_message = "All prefix values must contain only valid S3 prefix characters."
  }

  validation {
    condition = alltrue([
      for item in var.write_access_principals :
      (length(item.principals) > 0)
    ])
    error_message = "Each principals list must contain at least one principal."
  }
}

variable "delete_access_principals" {
  description = "The AWS principal(s) that can delete objects in the bucket scoped by prefix."
  type = list(object({
    prefix     = string
    principals = list(string)
  }))
  default = []

  validation {
    condition = alltrue([
      for item in var.delete_access_principals :
      can(regex("^[a-zA-Z0-9!_.*'()-/]*$", item.prefix))
    ])
    error_message = "All prefix values must contain only valid S3 prefix characters."
  }

  validation {
    condition = alltrue([
      for item in var.delete_access_principals :
      (length(item.principals) > 0)
    ])
    error_message = "Each principals list must contain at least one principal."
  }
}

variable "cloudfront_distribution_arns" {
  description = "The ARN(s) of the CloudFront distributions that have read-only access to the public items in the bucket."
  type        = list(string)
  default     = []
}