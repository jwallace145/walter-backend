resource "aws_lambda_event_source_mapping" "sqs_lambda_mapping" {
  event_source_arn                   = var.queue_arn
  function_name                      = var.function_name
  batch_size                         = var.batch_size
  maximum_batching_window_in_seconds = var.maximum_batching_window_in_seconds
  enabled                            = var.enabled
  function_response_types            = var.function_response_types

  scaling_config {
    maximum_concurrency = var.maximum_concurrency
  }
}
