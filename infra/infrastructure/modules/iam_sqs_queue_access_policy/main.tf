data "aws_iam_policy_document" "this" {
  statement {
    sid    = "SQSConsumePermissions"
    effect = "Allow"

    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:ChangeMessageVisibility",
      "sqs:GetQueueAttributes",
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
