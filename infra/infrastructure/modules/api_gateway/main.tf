resource "aws_api_gateway_rest_api" "api" {
  name        = var.name
  description = var.description

  endpoint_configuration {
    types = ["EDGE"]
  }
}

resource "aws_api_gateway_usage_plan" "usage_plan" {
  name        = "${var.name}-UsagePlan-${var.domain}"
  description = "The usage plan for making API calls to WalterBackend API. (${var.domain})"

  api_stages {
    api_id = aws_api_gateway_rest_api.api.id
    stage  = aws_api_gateway_stage.api_stage.stage_name
  }

  throttle_settings {
    rate_limit  = var.rate_limit
    burst_limit = var.burst_limit
  }

  depends_on = [aws_api_gateway_deployment.api_deployment]
}

resource "aws_api_gateway_usage_plan_key" "usage_plan_key" {
  key_id        = aws_api_gateway_api_key.api_key.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.usage_plan.id
}

resource "aws_api_gateway_api_key" "api_key" {
  name  = "${var.name}-Key-${var.domain}"
  value = var.api_key_value
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

  // API Access Logs Settings
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_access_logs.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      caller         = "$context.identity.caller"
      user           = "$context.identity.user"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      resourcePath   = "$context.resourcePath"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
      userAgent      = "$context.identity.userAgent"
    })
  }
}

// Enable API execution logs with request/response tracing enabled
resource "aws_api_gateway_method_settings" "api_log_settings" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  stage_name  = aws_api_gateway_stage.api_stage.stage_name
  method_path = "*/*"

  settings {
    logging_level      = "INFO"
    metrics_enabled    = true
    data_trace_enabled = true
  }
}

/***********
 * Logging *
 ***********/

// API Access Logs - includes caller information, api path, api method, etc. (see access_log_settings)
resource "aws_cloudwatch_log_group" "api_access_logs" {
  name              = "/aws/apigateway/${aws_api_gateway_rest_api.api.name}/${var.stage_name}/access"
  retention_in_days = var.log_retention_in_days
}

// API Execution Logs - contains the caller request and API response as well as any API Gateway errors (separate from function application logs)
resource "aws_cloudwatch_log_group" "api_execution_logs" {
  name              = "API-Gateway-Execution-Logs_${aws_api_gateway_rest_api.api.id}/${aws_api_gateway_stage.api_stage.stage_name}"
  retention_in_days = var.log_retention_in_days
}
