variable "rest_api_id" {
  description = "The ID of the REST API"
  type        = string
}

variable "parent_resource_id" {
  description = "The ID of the parent resource"
  type        = string
}

variable "path_part" {
  description = "The path part for the resource (e.g., 'login', 'users')"
  type        = string
}

variable "http_method" {
  description = "The HTTP method (GET, POST, PUT, DELETE)"
  type        = string
}

variable "lambda_invoke_arn" {
  description = "The Lambda function invoke ARN"
  type        = string
}

variable "enable_cors" {
  description = "Whether to enable CORS for this endpoint"
  type        = bool
  default     = false
}