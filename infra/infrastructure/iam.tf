/******************************
 * WalterBackend API IAM Role *
 ******************************/

# API IAM role requires full access to all DynamoDB tables and Secrets Manager secrets

module "api_role" {
  source      = "./modules/iam_lambda_execution_role"
  name        = "api-role-${var.domain}"
  description = "The IAM role used by the WalterBackend-API-${var.domain} Lambda function to process API requests."
  policies = {
    api_secrets_access = module.api_role_secrets_access.policy_arn,
    api_db_access      = module.api_role_db_access.policy_arn
  }
}

module "api_role_db_access" {
  source      = "./modules/iam_dynamodb_access_policy"
  policy_name = "api-db-access-policy"
  table_names = [
    local.USERS_TABLE,
    local.SESSIONS_TABLE,
    local.ACCOUNTS_TABLE,
    local.TRANSACTIONS_TABLE,
    local.SECURITIES_TABLE,
    local.HOLDINGS_TABLE
  ]
}

module "api_role_secrets_access" {
  source      = "./modules/iam_secrets_manager_access_policy"
  policy_name = "api-secrets-access-policy"
  secret_names = [
    local.AUTH_SECRETS,
    local.DATADOG_SECRET,
    local.POLYGON_SECRET,
    local.PLAID_SECRET,
    local.STRIPE_SECRET
  ]
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

module "workflow_role_db_access" {
  source      = "./modules/iam_dynamodb_access_policy"
  policy_name = "workflow-db-access-policy"
  table_names = [
    local.SECURITIES_TABLE,
  ]
}

# UpdatePrices workflow requires access to the Polygon API key to
# get the latest pricing data

module "workflow_role_secrets_access" {
  source      = "./modules/iam_secrets_manager_access_policy"
  policy_name = "workflow-secrets-access-policy"
  secret_names = [
    local.POLYGON_SECRET,
  ]
}

# SyncTransactions workflow requires queue access to process
# webhook and adhoc sync transaction requests

module "workflow_role_queue_access" {
  source = "./modules/iam_sqs_queue_access_policy"
  name   = "workflow-queue-access-policy"
  queue_arns = [
    module.queues["sync_transactions"].queue_arn,
    module.queues["sync_transactions"].dead_letter_queue_arn
  ]
}
