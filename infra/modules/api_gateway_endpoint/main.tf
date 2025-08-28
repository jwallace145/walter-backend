resource "aws_api_gateway_resource" "endpoint" {
  rest_api_id = var.rest_api_id
  parent_id   = var.parent_resource_id
  path_part   = var.path_part
}

resource "aws_api_gateway_method" "endpoint_method" {
  rest_api_id   = var.rest_api_id
  resource_id   = aws_api_gateway_resource.endpoint.id
  http_method   = var.http_method
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "endpoint_integration" {
  rest_api_id             = var.rest_api_id
  resource_id             = aws_api_gateway_resource.endpoint.id
  http_method             = aws_api_gateway_method.endpoint_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.lambda_invoke_arn
}

# Optional CORS
module "cors" {
  source = "../api_gateway_cors"
  count  = var.enable_cors ? 1 : 0

  rest_api_id = var.rest_api_id
  resource_id = aws_api_gateway_resource.endpoint.id
}