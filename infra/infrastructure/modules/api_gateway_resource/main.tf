resource "aws_api_gateway_resource" "endpoint" {
  rest_api_id = var.rest_api_id
  parent_id   = var.parent_resource_id
  path_part   = var.path_part
}

# Optional CORS (only needed once per resource)
module "cors" {
  source = "../api_gateway_cors"
  count  = var.enable_cors ? 1 : 0

  rest_api_id = var.rest_api_id
  resource_id = aws_api_gateway_resource.endpoint.id
}
