variable "name" {
  description = "The name of the API Gateway."
  type        = string
}

variable "description" {
  description = "The description of the API Gateway."
  type        = string
}

variable "function_name" {
  description = "The name of the Lambda function the API Gateway invokes."
  type        = string
}

variable "alias_name" {
  description = "The name of the alias used to increment versions of the Lambda function."
  type        = string
}

variable "image_digest" {
  description = "The image digest of the image used for the Lambda functions to trigger new API deployments."
  type        = string
}

variable "stage_name" {
  description = "The name of the stage to create for the API Gateway."
  type        = string
}
