output "method_id" {
  description = "The ID of the API Gateway method"
  value       = aws_api_gateway_method.endpoint_method.id
}

output "integration_id" {
  description = "The ID of the API Gateway integration"
  value       = aws_api_gateway_integration.endpoint_integration.id
}