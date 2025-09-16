/*********************************
 * WalterBackend Canary IAM Role *
 *********************************/

# Canary IAM role requires limited access to DynamoDB tables and Secrets Manager secrets

module "canary_role" {
  source      = "./modules/iam_lambda_execution_role"
  name        = "WalterBackend-Canary-Base-Role-${var.domain}"
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
    module.users_table.table_name,
    module.sessions_table.table_name
  ]
}

# canary requires access to auth secrets to create authenticated sessions
module "canary_role_secrets_access" {
  source      = "./modules/iam_secrets_manager_access_policy"
  policy_name = "canary-secrets-access-policy"
  secret_names = [
    module.secrets["Auth"].secret_name
  ]
}


