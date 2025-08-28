data "aws_partition" "current" {}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

locals {
  table_arns = [
    for name in var.table_names :
    "arn:${data.aws_partition.current.partition}:dynamodb:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:table/${name}"
  ]

  table_index_arns = [
    for name in var.table_names :
    "arn:${data.aws_partition.current.partition}:dynamodb:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:table/${name}/index/*"
  ]
}

data "aws_iam_policy_document" "this" {
  statement {
    sid = "DynamoDBReadAccess"

    actions = [
      "dynamodb:BatchGetItem",
      "dynamodb:DescribeTable",
      "dynamodb:GetItem",
      "dynamodb:Query",
      "dynamodb:Scan",
      "dynamodb:ListTagsOfResource"
    ]

    resources = concat(local.table_arns, local.table_index_arns)
  }

  statement {
    sid = "DynamoDBWriteAccess"

    actions = [
      "dynamodb:BatchWriteItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem"
    ]

    resources = local.table_arns
  }

  statement {
    sid = "DynamoDBDeleteItemAccess"

    actions = [
      "dynamodb:DeleteItem"
    ]

    resources = local.table_arns
  }
}

resource "aws_iam_policy" "this" {
  name   = var.policy_name
  policy = data.aws_iam_policy_document.this.json
}