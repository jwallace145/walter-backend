locals {
  CANARY_ROLES = {
    login = {
      name        = "Login"
      description = "The IAM role used by the Login canary to test API health. (${var.domain})"
      secrets = [
        module.secrets["Auth"].secret_name
      ]
      read_table_access_arns = [
        module.users_table.table_arn,
        module.sessions_table.table_arn
      ]
      write_table_access_arns = [
        module.users_table.table_arn,
        module.sessions_table.table_arn
      ]
      delete_table_access_arns = []
    }

    refresh = {
      name        = "Refresh"
      description = "The IAM role used by the Refresh canary to test API health. (${var.domain})"
      secrets = [
        module.secrets["Auth"].secret_name
      ]
      read_table_access_arns = [
        module.users_table.table_arn,
        module.sessions_table.table_arn
      ]
      write_table_access_arns = [
        module.users_table.table_arn,
        module.sessions_table.table_arn
      ]
      delete_table_access_arns = []
    }

    logout = {
      name        = "Logout"
      description = "The IAM role used by the Logout canary to test API health. (${var.domain})"
      secrets = [
        module.secrets["Auth"].secret_name
      ]
      read_table_access_arns = [
        module.users_table.table_arn,
        module.sessions_table.table_arn
      ]
      write_table_access_arns = [
        module.users_table.table_arn,
        module.sessions_table.table_arn
      ]
      delete_table_access_arns = []
    }

    get_user = {
      name        = "GetUser"
      description = "The IAM role used by the GetUser canary to test API health. (${var.domain})"
      secrets = [
        module.secrets["Auth"].secret_name
      ]
      read_table_access_arns = [
        module.users_table.table_arn,
        module.sessions_table.table_arn
      ]
      write_table_access_arns = [
        module.users_table.table_arn,
        module.sessions_table.table_arn
      ]
      delete_table_access_arns = []
    }

    create_user = {
      name        = "CreateUser"
      description = "The IAM role used by the CreateUser canary to test API health. (${var.domain})"
      secrets = [
        module.secrets["Auth"].secret_name
      ]
      read_table_access_arns = [
        module.users_table.table_arn,
        module.sessions_table.table_arn
      ]
      write_table_access_arns = [
        module.users_table.table_arn,
        module.sessions_table.table_arn
      ]
      delete_table_access_arns = [
        module.users_table.table_arn,
      ]
    }

    get_accounts = {
      name        = "GetAccounts"
      description = "The IAM role used by the GetAccounts canary to test API health. (${var.domain})"
      secrets = [
        module.secrets["Auth"].secret_name
      ]
      read_table_access_arns = [
        module.users_table.table_arn,
        module.sessions_table.table_arn
      ]
      write_table_access_arns = [
        module.users_table.table_arn,
        module.sessions_table.table_arn
      ]
      delete_table_access_arns = []
    }

    get_transactions = {
      name        = "GetTransactions"
      description = "The IAM role used by the GetTransactions canary to test API health. (${var.domain})"
      secrets = [
        module.secrets["Auth"].secret_name
      ]
      read_table_access_arns = [
        module.users_table.table_arn,
        module.sessions_table.table_arn
      ]
      write_table_access_arns = [
        module.users_table.table_arn,
        module.sessions_table.table_arn
      ]
      delete_table_access_arns = []
    }
  }
}

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
    canary_kms_access     = aws_iam_policy.canary_kms_access_policy.arn
  }
}

# canary requires access to users and sessions tables to create
# sessions for the canary user to test authenticated APIs
module "canary_role_db_access" {
  source      = "./modules/iam_dynamodb_access_policy"
  policy_name = "canary-db-access-policy"
  read_access_table_arns = [
    module.users_table.table_arn,
    module.sessions_table.table_arn
  ]
  write_access_table_arns = [
    module.users_table.table_arn,
    module.sessions_table.table_arn
  ]
  delete_access_table_arns = [
    module.users_table.table_arn # CreateUser canary needs to be able to delete test user after creation
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

resource "aws_iam_policy" "canary_kms_access_policy" {
  name        = "WalterBackend-Canary-KMS-Policy-${var.domain}"
  description = "The IAM policy used to encrypt and decrypt information with the given KMS keys for the WalterBackend canary."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "kms:*"
        ]
        Effect = "Allow"
        Resource = [
          module.functions["canary"].kms_key_arn
        ]
      }
    ]
  })
}

module "canary_roles" {
  for_each                      = local.CANARY_ROLES
  source                        = "./modules/canary_iam_roles"
  name                          = each.value.name
  domain                        = var.domain
  description                   = each.value.description
  secret_names                  = each.value.secrets
  read_table_access_arns        = each.value.read_table_access_arns
  write_table_access_arns       = each.value.write_table_access_arns
  delete_table_access_arns      = each.value.delete_table_access_arns
  canary_base_role              = module.canary_role.arn
  assume_canary_role_principals = var.canary_assume_role_additional_principals
}


