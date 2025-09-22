locals {
  API_ROLE_NAME                       = "WalterBackend-API-${var.name}-Role-${var.domain}"
  API_ROLE_SECRETS_ACCESS_POLICY_NAME = "WalterBackend-API-${var.name}-Secrets-Policy-${var.domain}"
  API_ROLE_DB_ACCESS_POLICY_NAME      = "WalterBackend-API-${var.name}-DB-Policy-${var.domain}"
  API_ROLE_SQS_ACCESS_POLICY_NAME     = "WalterBackend-API-${var.name}-SQS-Policy-${var.domain}"
}

resource "aws_iam_role" "api_iam_role" {
  name               = local.API_ROLE_NAME
  assume_role_policy = data.aws_iam_policy_document.api_iam_role_trust_policy.json
}

data "aws_iam_policy_document" "api_iam_role_trust_policy" {
  statement {
    effect = "Allow"

    actions = ["sts:AssumeRole"]

    principals {
      type        = "AWS"
      identifiers = concat([var.api_base_role], var.assume_api_role_principals)
    }
  }
}

resource "aws_iam_role_policy_attachment" "lambda_execution_access_attachment" {
  role       = aws_iam_role.api_iam_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role_policy_attachment" "secrets_access_attachment" {
  count      = length(var.secret_names) > 0 ? 1 : 0
  role       = aws_iam_role.api_iam_role.name
  policy_arn = module.api_iam_role_secrets_access[0].policy_arn
}

module "api_iam_role_secrets_access" {
  count        = length(var.secret_names) > 0 ? 1 : 0
  source       = "../iam_secrets_manager_access_policy"
  policy_name  = local.API_ROLE_SECRETS_ACCESS_POLICY_NAME
  secret_names = var.secret_names
}

resource "aws_iam_role_policy_attachment" "db_access_attachment" {
  count      = length(concat(var.read_table_access_arns, var.write_table_access_arns, var.delete_table_access_arns)) > 0 ? 1 : 0
  role       = aws_iam_role.api_iam_role.name
  policy_arn = module.api_iam_role_db_access[0].policy_arn
}

module "api_iam_role_db_access" {
  count                    = length(concat(var.read_table_access_arns, var.write_table_access_arns, var.delete_table_access_arns)) > 0 ? 1 : 0
  source                   = "../iam_dynamodb_access_policy"
  policy_name              = local.API_ROLE_DB_ACCESS_POLICY_NAME
  read_access_table_arns   = var.read_table_access_arns
  write_access_table_arns  = var.write_table_access_arns
  delete_access_table_arns = var.delete_table_access_arns
}

resource "aws_iam_role_policy_attachment" "sqs_access_attachment" {
  count      = length(var.send_message_access_queue_arns) > 0 ? 1 : 0
  role       = aws_iam_role.api_iam_role.name
  policy_arn = module.api_iam_role_sqs_access[0].policy_arn
}

module "api_iam_role_sqs_access" {
  count       = length(var.send_message_access_queue_arns) > 0 ? 1 : 0
  source      = "../iam_sqs_queue_access_policy"
  name        = local.API_ROLE_SQS_ACCESS_POLICY_NAME
  queue_arns  = var.send_message_access_queue_arns
  access_type = "producer"
}


