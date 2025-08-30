variable "rest_api_id" {
  description = "The ID of the API Gateway REST API"
  type        = string
}

variable "parent_resource_id" {
  description = "The ID of the parent resource"
  type        = string
}

variable "path_part" {
  description = "The path part for this resource"
  type        = string
}

variable "enable_cors" {
  description = "Whether to enable CORS for this resource"
  type        = bool
  default     = false
}
