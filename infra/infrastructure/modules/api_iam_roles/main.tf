module "api_role" {
  source      = "../iam_lambda_execution_role"
  name        = "WalterBackend-API-${var.name}-Role-${var.domain}"
  description = var.description
  policies = {
    api_role_secrets_access = module.api_role_secrets_access.policy_arn
    api_role_db_access      = module.api_role_db_access.policy_arn
  }
}

module "api_role_secrets_access" {
  source       = "../iam_secrets_manager_access_policy"
  policy_name  = "WalterBackend-API-${var.name}-Secrets-Policy-${var.domain}"
  secret_names = var.secret_names
}

module "api_role_db_access" {
  source      = "../iam_dynamodb_access_policy"
  policy_name = "WalterBackend-API-${var.name}-DB-Policy-${var.domain}"
  table_names = var.table_names
}


