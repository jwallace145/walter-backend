/******************************
 * WalterBackend API IAM Role *
 ******************************/

# API IAM role requires full access to all DynamoDB tables and Secrets Manager secrets

module "api_role" {
  source      = "./modules/iam_lambda_execution_role"
  name        = "WalterBackend-API-Role-${var.domain}"
  description = "The IAM role used by the WalterBackend API Lambda function to process API requests. (${var.domain})"
  policies = {
    assume_api_roles_policy = aws_iam_policy.api_assume_role_policy.arn
  }
}

resource "aws_iam_policy" "api_assume_role_policy" {
  name        = "WalterBackend-API-Base-Policy-${var.domain}"
  description = "The base IAM policy for the WalterBackend API function used to assume API-specific execution roles."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "sts:AssumeRole",
        ]
        Effect = "Allow"
        Resource = [
          module.api_roles["login"].role_arn,
          module.api_roles["logout"].role_arn,
          module.api_roles["refresh"].role_arn,
          module.api_roles["get_user"].role_arn,
          module.api_roles["create_user"].role_arn,
          module.api_roles["update_user"].role_arn,
          module.api_roles["get_accounts"].role_arn,
          module.api_roles["create_account"].role_arn,
          module.api_roles["update_account"].role_arn,
          module.api_roles["delete_account"].role_arn,
          module.api_roles["get_transactions"].role_arn,
          module.api_roles["add_transaction"].role_arn,
          module.api_roles["edit_transaction"].role_arn,
          module.api_roles["delete_transaction"].role_arn,
          module.api_roles["create_link_token"].role_arn,
          module.api_roles["exchange_public_token"].role_arn,
          module.api_roles["sync_transactions"].role_arn
        ]
      },
    ]
  })
}

/*********************************
 * WalterBackend Canary IAM Role *
 *********************************/

# Canary IAM role requires limited access to DynamoDB tables and Secrets Manager secrets

module "canary_role" {
  source      = "./modules/iam_lambda_execution_role"
  name        = "canary-role-${var.domain}"
  description = "The IAM role used by the WalterBackend-Canary-${var.domain} Lambda function to test API health."
  policies = {
    canary_db_access      = module.canary_role_db_access.policy_arn,
    canary_secrets_access = module.canary_role_secrets_access.policy_arn
  }
}

# canary requires access to users and sessions tables to create
# sessions for the canary user to test authenticated APIs
module "canary_role_db_access" {
  source      = "./modules/iam_dynamodb_access_policy"
  policy_name = "canary-db-access-policy"
  table_names = [
    local.USERS_TABLE,
    local.SESSIONS_TABLE,
  ]
}

# canary requires access to auth secrets to create authenticated sessions
module "canary_role_secrets_access" {
  source      = "./modules/iam_secrets_manager_access_policy"
  policy_name = "canary-secrets-access-policy"
  secret_names = [
    local.AUTH_SECRETS,
    module.secrets["Auth"].secret_name
  ]
}

/***********************************
 * WalterBackend Workflow IAM Role *
 ***********************************/

# Workflow IAM role requires limited access to DynamoDB tables and Secrets Manager secrets

module "workflow_role" {
  source      = "./modules/iam_lambda_execution_role"
  name        = "workflow-role-${var.domain}"
  description = "The IAM role used by the WalterBackend-Workflow-${var.domain} Lambda function to process asynchronous workflows."
  policies = {
    worklow_db_access      = module.workflow_role_db_access.policy_arn
    workflow_secret_access = module.workflow_role_secrets_access.policy_arn
    workflow_queue_access  = module.workflow_role_queue_access.policy_arn
  }
}

# UpdatePrices workflow requires access to Securities table
# SyncTransactions workflow requires access to Users, Accounts, and Transactions tables

module "workflow_role_db_access" {
  source      = "./modules/iam_dynamodb_access_policy"
  policy_name = "workflow-db-access-policy"
  table_names = [
    local.SECURITIES_TABLE,
    local.USERS_TABLE,
    local.ACCOUNTS_TABLE,
    local.TRANSACTIONS_TABLE
  ]
}

# UpdatePrices workflow requires access to the Polygon API key to
# get the latest pricing data

module "workflow_role_secrets_access" {
  source      = "./modules/iam_secrets_manager_access_policy"
  policy_name = "workflow-secrets-access-policy"
  secret_names = [
    local.POLYGON_SECRET,
    local.PLAID_SECRET,
    module.secrets["Polygon"].secret_name,
    module.secrets["Plaid"].secret_name
  ]
}

# SyncTransactions workflow requires queue access to process
# webhook and adhoc sync transaction requests

module "workflow_role_queue_access" {
  source      = "./modules/iam_sqs_queue_access_policy"
  name        = "workflow-queue-access-policy"
  access_type = "consumer"
  queue_arns = [
    module.queues["sync_transactions"].queue_arn,
    module.queues["sync_transactions"].dead_letter_queue_arn
  ]
}
