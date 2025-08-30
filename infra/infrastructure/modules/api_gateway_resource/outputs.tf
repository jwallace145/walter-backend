output "resource_id" {
  description = "The ID of the created API Gateway resource"
  value       = aws_api_gateway_resource.endpoint.id
}

output "resource_path" {
  description = "The full path of the resource"
  value       = aws_api_gateway_resource.endpoint.path
}
