variable "rest_api_id" {
  description = "The ID of the REST API"
  type        = string
}

variable "resource_id" {
  description = "The ID of the API Gateway resource"
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