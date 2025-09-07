output "queue_arn" {
  value       = aws_sqs_queue.queue.arn
  description = "The ARN of the SQS queue."
}

output "dead_letter_queue_arn" {
  value       = aws_sqs_queue.dead_letter_queue.arn
  description = "The ARN of the DLQ."
}