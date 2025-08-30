output "resource_id" {
  description = "The ID of the created API Gateway resource"
  value       = aws_api_gateway_resource.endpoint.id
}

output "method_id" {
  description = "The ID of the API Gateway method"
  value       = aws_api_gateway_method.endpoint_method.id
}

output "integration_id" {
  description = "The ID of the API Gateway integration"
  value       = aws_api_gateway_integration.endpoint_integration.id
}

output "cors_method_id" {
  description = "The ID of the CORS OPTIONS method (if enabled)"
  value       = var.enable_cors ? module.cors[0].cors_method_id : null
}