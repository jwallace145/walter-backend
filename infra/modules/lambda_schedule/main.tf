resource "aws_cloudwatch_event_rule" "this" {
  name                = var.name
  description         = var.description
  schedule_expression = var.schedule_expression
  state               = "ENABLED"
}

resource "aws_cloudwatch_event_target" "this_with_input" {
  count     = var.input == null ? 0 : 1
  rule      = aws_cloudwatch_event_rule.this.name
  target_id = var.target_id
  arn       = var.lambda_function_arn
  input     = var.input
}

resource "aws_cloudwatch_event_target" "this_no_input" {
  count     = var.input == null ? 1 : 0
  rule      = aws_cloudwatch_event_rule.this.name
  target_id = var.target_id
  arn       = var.lambda_function_arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "${var.name}-allow-eventbridge"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_arn
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.this.arn
}
