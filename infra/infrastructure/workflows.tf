locals {
  WORKFLOW_ROLES = {
    update_security_prices = {
      name        = "UpdateSecurityPrices"
      description = "The role that is assumed by the WalterBackend Workflows function to execute the UpdateSecurityPrices workflow. (${var.domain})"
      secrets = [
        module.secrets["Polygon"].secret_name
      ]
      tables = [
        module.securities_table.table_name
      ]
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
      tables = [
        module.users_table.table_name,
        module.accounts_table.table_name,
        module.transactions_table.table_name
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
  name        = "WalterBackend-Workflow-Base-Policy-${var.domain}"
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
      },
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
  for_each              = local.WORKFLOW_ROLES
  source                = "./modules/workflow_iam_role"
  name                  = each.value.name
  domain                = var.domain
  description           = each.value.description
  secrets_access        = each.value.secrets
  tables_access         = each.value.tables
  workflow_base_role    = module.workflow_base_role.arn
  additional_principals = var.workflow_assume_role_additional_principals
}

