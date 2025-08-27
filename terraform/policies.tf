locals {
  walterdb_table_arns = [
    for table in local.walterdb_tables :
    "arn:${local.aws_partition}:dynamodb:${local.aws_region}:${local.aws_account_id}:table/${table}"
  ]

  walterdb_index_arns = [
    for index in local.walterdb_indexes :
    "arn:${local.aws_partition}:dynamodb:${local.aws_region}:${local.aws_account_id}:table/${index.table}/index/${index.name}"
  ]

  walterbackend_secret_arn_prefixes = [
    for secret in local.walterbackend_secrets :
    "arn:${local.aws_partition}:secretsmanager:${local.aws_region}:${local.aws_account_id}:secret:${secret}-*"
  ]
}

resource "aws_iam_policy" "secrets_r_policy" {
  name        = "walterbackend-secrets-${var.domain}"
  description = "This policy grants read permissions to all the secrets used by WalterBackend (${var.domain})."
  policy      = data.aws_iam_policy_document.secrets_r_policy_document.json
}


resource "aws_iam_policy" "db_rw_policy" {
  name        = "walterdb-rw-${var.domain}"
  description = "This policy grants read and write permissions to every table included in WalterDB."
  policy      = data.aws_iam_policy_document.db_rw_policy_document.json
}

data "aws_iam_policy_document" "secrets_r_policy_document" {
  statement {
    sid    = "SecretsReadAccess"
    effect = "Allow"

    actions = [
      "secretsmanager:GetSecretValue"
    ]

    resources = local.walterbackend_secret_arn_prefixes
  }
}

data "aws_iam_policy_document" "db_rw_policy_document" {
  statement {
    sid    = "WalterDBReadWriteAccess"
    effect = "Allow"

    actions = [
      # read
      "dynamodb:BatchGetItem",
      "dynamodb:GetItem",
      "dynamodb:Query",
      "dynamodb:Scan",
      "dynamodb:DescribeTable",

      # write
      "dynamodb:BatchWriteItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",

      # delete
      "dynamodb:DeleteItem",
    ]

    resources = local.walterdb_table_arns
  }

  statement {
    sid    = "WalterDBQueryIndicesAccess"
    effect = "Allow"

    actions = [
      "dynamodb:Query"
    ]

    resources = local.walterdb_index_arns
  }
}
