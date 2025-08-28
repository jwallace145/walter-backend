resource "aws_api_gateway_method" "cors_method" {
  rest_api_id   = var.rest_api_id
  resource_id   = var.resource_id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "cors_integration" {
  rest_api_id = var.rest_api_id
  resource_id = var.resource_id
  http_method = aws_api_gateway_method.cors_method.http_method

  type                 = "MOCK"
  passthrough_behavior = "WHEN_NO_MATCH"

  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }

  depends_on = [aws_api_gateway_method.cors_method]
}

resource "aws_api_gateway_method_response" "cors_method_response" {
  rest_api_id = var.rest_api_id
  resource_id = var.resource_id
  http_method = aws_api_gateway_method.cors_method.http_method
  status_code = "200"

  response_models = {
    "application/json" = "Empty"
  }

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers"     = false
    "method.response.header.Access-Control-Allow-Methods"     = false
    "method.response.header.Access-Control-Allow-Origin"      = false
    "method.response.header.Access-Control-Allow-Credentials" = var.allow_credentials
    "method.response.header.Access-Control-Max-Age"           = false
  }

  depends_on = [aws_api_gateway_method.cors_method]
}

resource "aws_api_gateway_integration_response" "cors_integration_response" {
  rest_api_id = var.rest_api_id
  resource_id = var.resource_id
  http_method = aws_api_gateway_method.cors_method.http_method
  status_code = aws_api_gateway_method_response.cors_method_response.status_code

  response_parameters = merge(
    {
      "method.response.header.Access-Control-Allow-Headers" = "'${var.allow_headers}'"
      "method.response.header.Access-Control-Allow-Methods" = "'${var.allow_methods}'"
      "method.response.header.Access-Control-Allow-Origin"  = "'${var.allow_origin}'"
      "method.response.header.Access-Control-Max-Age"       = "'${var.max_age}'"
    },
    var.allow_credentials ? {
      "method.response.header.Access-Control-Allow-Credentials" = "'true'"
    } : {}
  )

  response_templates = {
    "application/json" = ""
  }

  depends_on = [
    aws_api_gateway_integration.cors_integration,
    aws_api_gateway_method_response.cors_method_response
  ]
}