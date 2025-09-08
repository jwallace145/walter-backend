resource "aws_sqs_queue" "queue" {
  name                      = "${var.service}-${var.name}-Queue-${var.domain}"
  sqs_managed_sse_enabled   = true
  delay_seconds             = 0
  max_message_size          = 4096
  message_retention_seconds = 86400
  receive_wait_time_seconds = 10
}

resource "aws_sqs_queue" "dead_letter_queue" {
  name = "${var.service}-${var.name}-DLQ-${var.domain}"
  redrive_allow_policy = jsonencode({
    redrivePermission = "byQueue",
    sourceQueueArns   = [aws_sqs_queue.queue.arn]
  })
}

resource "aws_sqs_queue_redrive_policy" "redrive_policy" {
  queue_url = aws_sqs_queue.queue.id
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dead_letter_queue.arn
    maxReceiveCount     = var.redrive_policy_max_receive_count
  })
}