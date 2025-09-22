locals {
  WORKFLOW_ROLE_NAME                  = "WalterBackend-Workflow-${var.name}-Role-${var.domain}"
  WORKFLOW_SECRETS_ACCESS_POLICY_NAME = "WalterBackend-Workflow-${var.name}-Secrets-Policy-${var.domain}"
  WORKFLOW_DB_ACCESS_POLICY_NAME      = "WalterBackend-Workflow-${var.name}-DB-Policy-${var.domain}"
  WORKFLOW_SQS_ACCESS_POLICY_NAME     = "WalterBackend-Workflow-${var.domain}-SQS-Policy-${var.domain}"
}

resource "aws_iam_role" "workflow_role" {
  name               = local.WORKFLOW_ROLE_NAME
  assume_role_policy = data.aws_iam_policy_document.workflow_role_trust_policy.json
}

data "aws_iam_policy_document" "workflow_role_trust_policy" {
  statement {
    effect = "Allow"

    actions = ["sts:AssumeRole"]

    principals {
      type        = "AWS"
      identifiers = concat([var.workflow_base_role], var.additional_principals)
    }
  }
}

resource "aws_iam_role_policy_attachment" "lambda_execution_access_attachment" {
  role       = aws_iam_role.workflow_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "secrets_access_attachment" {
  count      = length(var.secrets_access) > 0 ? 1 : 0
  role       = aws_iam_role.workflow_role.name
  policy_arn = module.workflow_role_secrets_access[0].policy_arn
}

module "workflow_role_secrets_access" {
  count        = length(var.secrets_access) > 0 ? 1 : 0
  source       = "../iam_secrets_manager_access_policy"
  policy_name  = local.WORKFLOW_SECRETS_ACCESS_POLICY_NAME
  secret_names = var.secrets_access
}

resource "aws_iam_role_policy_attachment" "db_access_attachment" {
  count      = length(concat(var.read_table_access_arns, var.write_table_access_arns, var.delete_table_access_arns)) > 0 ? 1 : 0
  role       = aws_iam_role.workflow_role.name
  policy_arn = module.workflow_role_db_access[0].policy_arn
}

module "workflow_role_db_access" {
  count                    = length(concat(var.read_table_access_arns, var.write_table_access_arns, var.delete_table_access_arns)) > 0 ? 1 : 0
  source                   = "../iam_dynamodb_access_policy"
  policy_name              = local.WORKFLOW_DB_ACCESS_POLICY_NAME
  read_access_table_arns   = var.read_table_access_arns
  write_access_table_arns  = var.write_table_access_arns
  delete_access_table_arns = var.delete_table_access_arns
}

resource "aws_iam_role_policy_attachment" "sqs_access_attachment" {
  count      = length(var.receive_message_access_queue_arns) > 0 ? 1 : 0
  role       = aws_iam_role.workflow_role.name
  policy_arn = module.workflow_role_sqs_access[0].policy_arn
}

module "workflow_role_sqs_access" {
  count       = length(var.receive_message_access_queue_arns) > 0 ? 1 : 0
  source      = "../iam_sqs_queue_access_policy"
  name        = local.WORKFLOW_SQS_ACCESS_POLICY_NAME
  queue_arns  = var.receive_message_access_queue_arns
  access_type = "consumer"
}
