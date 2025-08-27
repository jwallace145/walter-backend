locals {
  datadog_handler = "datadog_lambda.handler.handler"
}

resource "aws_lambda_function" "api" {
  function_name = "WalterBackend-API-${var.domain}"
  description   = "The entrypoint function for all APIs included in WalterBackend (${var.domain})."

  package_type = "Image"
  image_uri    = var.image_uri

  role = aws_iam_role.api_role.arn

  image_config {
    command = [local.datadog_handler]
  }

  timeout       = var.api_timeout_seconds
  memory_size   = var.api_lambda_memory_mb
  architectures = ["arm64"]

  environment {
    variables = {
      DD_LAMBDA_HANDLER = "walter.api_entrypoint"
      DD_LOG_LEVEL      = var.log_level
      DOMAIN            = var.domain
      LOG_LEVEL         = var.log_level
    }
  }

  publish = true
}

resource "aws_lambda_function" "workflows" {
  function_name = "WalterBackend-Workflow-${var.domain}"
  description   = "The entrypoint function for all asynchronous workflows in WalterBackend (${var.domain})."

  package_type = "Image"
  image_uri    = var.image_uri

  role = aws_iam_role.workflow_role.arn

  image_config {
    command = [local.datadog_handler]
  }

  timeout       = var.workflow_timeout_seconds
  memory_size   = var.workflow_lambda_memory_mb
  architectures = ["arm64"]

  environment {
    variables = {
      DD_LAMBDA_HANDLER = "walter.workflows_entrypoint"
      DD_LOG_LEVEL      = var.log_level
      DOMAIN            = var.domain
      LOG_LEVEL         = var.log_level
    }
  }

  publish = true
}

resource "aws_lambda_function" "canary" {
  function_name = "WalterBackend-Canary-${var.domain}"
  description   = "The single entrypoint for all API canaries in WalterBackend (${var.domain})"

  package_type = "Image"
  image_uri    = var.image_uri

  role = aws_iam_role.canary_role.arn

  image_config {
    command = [local.datadog_handler]
  }

  timeout       = var.canary_timeout_seconds
  memory_size   = var.canary_lambda_memory_mb
  architectures = ["arm64"]

  environment {
    variables = {
      DD_LAMBDA_HANDLER = "walter.canaries_entrypoint"
      DD_LOG_LEVEL      = var.log_level
      DOMAIN            = var.domain
      LOG_LEVEL         = var.log_level
    }
  }

  publish = true
}
