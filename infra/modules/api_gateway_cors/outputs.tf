output "cors_method_id" {
  description = "The ID of the CORS OPTIONS method"
  value       = aws_api_gateway_method.cors_method.id
}

output "cors_integration_id" {
  description = "The ID of the CORS integration"
  value       = aws_api_gateway_integration.cors_integration.id
}

output "cors_method_response_id" {
  description = "The ID of the CORS method response"
  value       = aws_api_gateway_method_response.cors_method_response.id
}

output "cors_integration_response_id" {
  description = "The ID of the CORS integration response"
  value       = aws_api_gateway_integration_response.cors_integration_response.id
}

output "cors_configuration" {
  description = "CORS configuration summary"
  value = {
    allow_origin      = var.allow_origin
    allow_methods     = var.allow_methods
    allow_headers     = var.allow_headers
    allow_credentials = var.allow_credentials
    max_age           = var.max_age
  }
}