locals {
  read_index_arns = [
    for arn in var.read_access_table_arns :
    "${arn}/index/*"
  ]
}

data "aws_iam_policy_document" "this" {
  dynamic "statement" {
    for_each = length(var.read_access_table_arns) > 0 ? [1] : []
    content {
      sid = "DynamoDBReadAccess"

      actions = [
        "dynamodb:BatchGetItem",
        "dynamodb:DescribeTable",
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:ListTagsOfResource"
      ]

      resources = concat(var.read_access_table_arns, local.read_index_arns)
    }
  }

  dynamic "statement" {
    for_each = length(var.write_access_table_arns) > 0 ? [1] : []
    content {
      sid = "DynamoDBWriteAccess"

      actions = [
        "dynamodb:BatchWriteItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem"
      ]

      resources = var.write_access_table_arns
    }
  }

  dynamic "statement" {
    for_each = length(var.delete_access_table_arns) > 0 ? [1] : []
    content {
      sid = "DynamoDBDeleteItemAccess"

      actions = [
        "dynamodb:DeleteItem"
      ]

      resources = var.delete_access_table_arns
    }
  }
}

resource "aws_iam_policy" "this" {
  name   = var.policy_name
  policy = data.aws_iam_policy_document.this.json
}