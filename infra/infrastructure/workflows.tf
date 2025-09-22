locals {
  WORKFLOW_ROLES = {
    update_security_prices = {
      name        = "UpdateSecurityPrices"
      description = "The role that is assumed by the WalterBackend Workflows function to execute the UpdateSecurityPrices workflow. (${var.domain})"
      secrets = [
        module.secrets["Polygon"].secret_name
      ]
      read_access_table_arns = [
        module.securities_table.table_arn
      ]
      write_access_table_arns = [
        module.securities_table.table_arn
      ]
      delete_access_table_arns   = []
      receive_message_queue_arns = []
      principals = [
        var.workflow_assume_role_additional_principals
      ]
    }

    sync_transactions = {
      name        = "SyncTransactions"
      description = "The role that is assumed by the WalterBackend Workflow function to execute the SyncTransactions workflow. (${var.domain})"
      secrets = [
        module.secrets["Plaid"].secret_name
      ]
      read_access_table_arns = [
        module.users_table.table_arn,
        module.accounts_table.table_arn,
        module.transactions_table.table_arn
      ]
      write_access_table_arns = [
        module.users_table.table_arn,
        module.accounts_table.table_arn,
        module.transactions_table.table_arn
      ]
      delete_access_table_arns = []
      receive_message_queue_arns = [
        module.queues["sync_transactions"].queue_arn
      ]
      principals = [
        var.workflow_assume_role_additional_principals
      ]
    }
  }
}

/**********************
 * Workflow IAM Roles *
 **********************/

module "workflow_base_role" {
  source      = "./modules/iam_lambda_execution_role"
  name        = "WalterBackend-Workflow-Base-Role-${var.domain}"
  description = "The IAM role used by the WalterBackend Workflow Lambda function to assume workflow-specific roles for execution. (${var.domain})"
  policies = {
    assume_workflow_roles_policy = aws_iam_policy.workflow_assume_role_policy.arn
  }
}

resource "aws_iam_policy" "workflow_assume_role_policy" {
  name        = "WalterBackend-Workflow-Base-Assume-Policy-${var.domain}"
  description = "The base IAM policy for the WalterBackend Workflow function used to assume workflow-specific execution roles."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "sts:AssumeRole",
        ]
        Effect = "Allow"
        Resource = [
          module.workflow_roles["update_security_prices"].role_arn,
          module.workflow_roles["sync_transactions"].role_arn
        ]
      }
    ]
  })
}

resource "aws_iam_policy" "workflow_kms_access_policy" {
  name        = "WalterBackend-Workflow-Base-KMS-Policy-${var.domain}"
  description = "The base IAM policy for the WalterBackend Workflow function used to encrypt and decrypt with KMS."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "kms:*"
        ]
        Effect = "Allow"
        Resource = [
          module.functions["workflow"].kms_key_arn
        ]
      }
    ]
  })
}

module "workflow_roles" {
  for_each                          = local.WORKFLOW_ROLES
  source                            = "./modules/workflow_iam_role"
  name                              = each.value.name
  domain                            = var.domain
  description                       = each.value.description
  secrets_access                    = each.value.secrets
  read_table_access_arns            = each.value.read_access_table_arns
  write_table_access_arns           = each.value.write_access_table_arns
  delete_table_access_arns          = each.value.delete_access_table_arns
  receive_message_access_queue_arns = each.value.receive_message_queue_arns
  workflow_base_role                = module.workflow_base_role.arn
  additional_principals             = var.workflow_assume_role_additional_principals
}

