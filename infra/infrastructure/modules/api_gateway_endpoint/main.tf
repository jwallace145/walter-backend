resource "aws_api_gateway_method" "endpoint_method" {
  rest_api_id   = var.rest_api_id
  resource_id   = var.resource_id
  http_method   = var.http_method
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "endpoint_integration" {
  rest_api_id             = var.rest_api_id
  resource_id             = var.resource_id
  http_method             = aws_api_gateway_method.endpoint_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.lambda_invoke_arn
}