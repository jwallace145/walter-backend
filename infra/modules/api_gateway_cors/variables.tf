variable "rest_api_id" {
  description = "The ID of the REST API"
  type        = string
}

variable "resource_id" {
  description = "The resource ID where CORS will be enabled"
  type        = string
}

variable "allow_origin" {
  description = "Allowed origins for CORS"
  type        = string
  default     = "*"
}

variable "allow_methods" {
  description = "Allowed HTTP methods"
  type        = string
  default     = "GET,POST,PUT,DELETE,OPTIONS"
}

variable "allow_headers" {
  description = "Allowed headers"
  type        = string
  default     = "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent"
}

variable "allow_credentials" {
  description = "Whether credentials are allowed"
  type        = bool
  default     = false
}

variable "max_age" {
  description = "How long the browser should cache preflight requests (in seconds)"
  type        = number
  default     = 86400 # 24 hours
}