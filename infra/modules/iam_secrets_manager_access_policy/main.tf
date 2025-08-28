data "aws_partition" "current" {}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

locals {
  # Secrets Manager requires the secret ARN with a trailing -* to cover all versions of the secret
  # We build ARNs from secret names to stay consistent with other modules (like DynamoDB)
  secret_arns = [
    for name in var.secret_names :
    "arn:${data.aws_partition.current.partition}:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:${name}-*"
  ]
}

data "aws_iam_policy_document" "this" {
  statement {
    sid = "SecretsManagerReadAccess"

    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret"
    ]

    resources = local.secret_arns
  }
}

resource "aws_iam_policy" "this" {
  name   = var.policy_name
  policy = data.aws_iam_policy_document.this.json
}
