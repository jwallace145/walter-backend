locals {
  is_consumer = lower(var.access_type) == "consumer"
}

data "aws_iam_policy_document" "this" {
  statement {
    sid    = local.is_consumer ? "SQSConsumePermissions" : "SQSProducePermissions"
    effect = "Allow"

    actions = local.is_consumer ? [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:ChangeMessageVisibility",
      "sqs:GetQueueAttributes",
      "sqs:GetQueueUrl"
      ] : [
      "sqs:SendMessage",
      "sqs:GetQueueUrl"
    ]

    resources = var.queue_arns
  }
}

resource "aws_iam_policy" "this" {
  name        = var.name
  description = var.description
  policy      = data.aws_iam_policy_document.this.json
  tags        = var.tags
}
