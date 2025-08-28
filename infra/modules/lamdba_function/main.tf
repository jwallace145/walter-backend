resource "aws_lambda_function" "this" {
  function_name = var.function_name
  description   = var.description

  package_type = "Image"
  image_uri    = var.image_uri

  role = var.role_arn

  image_config {
    # all lambdas use the datadog wrapper entrypoint to support
    # datadog metrics, the function specific entrypoint is set
    # as the DD_LAMBDA_HANDLER environment variable
    command = ["datadog_lambda.handler.handler"]
  }

  timeout       = var.timeout
  memory_size   = var.memory_size
  architectures = ["arm64"]

  environment {
    variables = {
      DD_LAMBDA_HANDLER = var.lambda_handler
      DD_LOG_LEVEL      = var.log_level
      DOMAIN            = var.domain
      LOG_LEVEL         = var.log_level
    }
  }

  publish = var.publish
}
