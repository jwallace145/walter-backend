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
      DD_API_KEY        = var.datadog_api_key
      DD_SITE           = var.datadog_site
      DOMAIN            = var.domain
      LOG_LEVEL         = var.log_level
    }
  }
}

resource "aws_lambda_alias" "release" {
  name             = var.alias_name
  description      = "The release alias of the WalterBackend function that points to the latest image."
  function_name    = aws_lambda_function.this.function_name
  function_version = var.function_version
}

resource "aws_lambda_provisioned_concurrency_config" "provisioned_concurrency" {
  function_name                     = aws_lambda_function.this.function_name
  provisioned_concurrent_executions = var.provisioned_concurrent_executions
  qualifier                         = aws_lambda_alias.release.name

  depends_on = [aws_lambda_alias.release]
}

resource "aws_cloudwatch_log_group" "log_group" {
  name              = "/aws/lambda/${aws_lambda_function.this.function_name}"
  retention_in_days = var.log_retention_in_days

  depends_on = [aws_lambda_function.this]
}
