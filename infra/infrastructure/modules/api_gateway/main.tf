resource "aws_api_gateway_rest_api" "api" {
  name        = var.name
  description = var.description

  endpoint_configuration {
    types = ["EDGE"]
  }
}

resource "aws_lambda_permission" "api_invoke_function" {
  statement_id  = "AllowAPIGatewayLambdaInvocation"
  action        = "lambda:InvokeFunction"
  function_name = var.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_api_gateway_rest_api.api.execution_arn}/*"
  qualifier  = var.alias_name
}

resource "aws_api_gateway_deployment" "api_deployment" {
  rest_api_id = aws_api_gateway_rest_api.api.id

  triggers = {
    redeployment = sha1(jsonencode([var.image_digest]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "api_stage" {
  deployment_id = aws_api_gateway_deployment.api_deployment.id
  rest_api_id   = aws_api_gateway_rest_api.api.id
  stage_name    = var.stage_name
}