locals {
  BASE_DOMAIN = "walterai.dev"
  NAME        = "WalterBackend-API"
  DESCRIPTION = "The API Gateway for all APIs served by WalterBackend."

  STAGE_NAME = "dev"

  # all api resources for walter backend api defined here
  RESOURCES = {
    login                 = { parent = "auth", path = "login", cors = true },
    refresh               = { parent = "auth", path = "refresh", cors = true },
    logout                = { parent = "auth", path = "logout", cors = true },
    users                 = { parent = "root", path = "users", cors = true },
    accounts              = { parent = "root", path = "accounts", cors = true },
    transactions          = { parent = "root", path = "transactions", cors = true },
    create-link-token     = { parent = "plaid", path = "create-link-token", cors = true }
    exchange-public-token = { parent = "plaid", path = "exchange-public-token", cors = true }
    sync-transactions     = { parent = "plaid", path = "sync-transactions", cors = true }
  }

  # all endpoints served by walter backend are defined here
  ENDPOINTS = {

    # authentication endpoints
    login   = { parent = "auth", path = "login", method = "POST" },
    logout  = { parent = "auth", path = "logout", method = "POST" },
    refresh = { parent = "auth", path = "refresh", method = "POST" },

    # user endpoints
    get_user    = { parent = "root", path = "users", method = "GET" },
    create_user = { parent = "root", path = "users", method = "POST" },
    update_user = { parent = "root", path = "users", method = "PUT" },

    # account endpoints
    get_accounts   = { parent = "root", path = "accounts", method = "GET" },
    create_account = { parent = "root", path = "accounts", method = "POST" },
    update_account = { parent = "root", path = "accounts", method = "PUT" },
    delete_account = { parent = "root", path = "accounts", method = "DELETE" },

    # transaction endpoints
    get_transactions   = { parent = "root", path = "transactions", method = "GET" },
    add_transaction    = { parent = "root", path = "transactions", method = "POST" },
    edit_transaction   = { parent = "root", path = "transactions", method = "PUT" },
    delete_transaction = { parent = "root", path = "transactions", method = "DELETE" },

    # plaid endpoints
    create_link_token     = { parent = "plaid", path = "create-link-token", method = "POST" },
    exchange_public_token = { parent = "plaid", path = "exchange-public-token", method = "POST" },
    sync_transactions     = { parent = "plaid", path = "sync-transactions", method = "POST" }
  }

  # used as a helper to get api gateway resource id from parent name
  PARENT_TO_RESOURCE_ID = {
    auth  = aws_api_gateway_resource.auth.id,
    plaid = aws_api_gateway_resource.plaid.id,
    root  = module.api.root_resource_id,
  }

  API_ROLES = {
    login = {
      name        = "Login"
      description = "The role used by the WalterBackend API function to execute the Login API. (${var.domain})"
      secrets = [
        module.secrets["Auth"].secret_name
      ]
      read_access_table_arns = [
        module.users_table.table_arn,
        module.sessions_table.table_arn
      ]
      write_access_table_arns = [
        module.users_table.table_arn,
        module.sessions_table.table_arn
      ]
      delete_access_table_arns = []
    }

    logout = {
      name        = "Logout"
      description = "The role used by the WalterBackend API function to execute the Logout API. (${var.domain})"
      secrets = [
        module.secrets["Auth"].secret_name
      ]
      read_access_table_arns = [
        module.users_table.table_arn,
        module.sessions_table.table_arn
      ]
      write_access_table_arns = [
        module.users_table.table_arn,
        module.sessions_table.table_arn
      ]
      delete_access_table_arns = []
    }

    refresh = {
      name        = "Refresh"
      description = "The role used by the WalterBackend API function to execute the Refresh API. (${var.domain})"
      secrets = [
        module.secrets["Auth"].secret_name
      ]
      read_access_table_arns = [
        module.users_table.table_arn,
        module.sessions_table.table_arn
      ]
      write_access_table_arns = [
        module.users_table.table_arn,
        module.sessions_table.table_arn
      ]
      delete_access_table_arns = []
    }

    get_user = {
      name        = "GetUser"
      description = "The role used by the WalterBackend API function to execute the GetUser API. (${var.domain})"
      secrets = [
        module.secrets["Auth"].secret_name
      ]
      read_access_table_arns = [
        module.users_table.table_arn,
        module.sessions_table.table_arn
      ]
      write_access_table_arns = [
        module.users_table.table_arn,
        module.sessions_table.table_arn
      ]
      delete_access_table_arns = []
    }

    create_user = {
      name        = "CreateUser"
      description = "The role used by the WalterBackend API function to execute the CreateUser API. (${var.domain})"
      secrets     = []
      read_access_table_arns = [
        module.users_table.table_arn
      ]
      write_access_table_arns = [
        module.users_table.table_arn
      ]
      delete_access_table_arns = []
    }

    update_user = {
      name        = "UpdateUser"
      description = "The role used by the WalterBackend API function to execute the UpdateUser API. (${var.domain})"
      secrets     = []
      read_access_table_arns = [
        module.users_table.table_arn
      ]
      write_access_table_arns = [
        module.users_table.table_arn
      ]
      delete_access_table_arns = []
    }

    get_accounts = {
      name        = "GetAccounts"
      description = "The role used by the WalterBackend API function to execute the GetAccounts API. (${var.domain})"
      secrets = [
        module.secrets["Auth"].secret_name
      ]
      read_access_table_arns = [
        module.accounts_table.table_arn,
        module.sessions_table.table_arn,
        module.users_table.table_arn,
        module.holdings_table.table_arn,
        module.securities_table.table_arn
      ]
      write_access_table_arns = [
        module.accounts_table.table_arn
      ]
      delete_access_table_arns = []
    }

    create_account = {
      name        = "CreateAccount"
      description = "The role used by the WalterBackend API function to execute the CreateAccount API. (${var.domain})"
      secrets = [
        module.secrets["Auth"].secret_name
      ]
      read_access_table_arns = [
        module.accounts_table.table_arn,
        module.sessions_table.table_arn,
        module.users_table.table_arn
      ]
      write_access_table_arns = [
        module.accounts_table.table_arn,
        module.sessions_table.table_arn,
        module.users_table.table_arn
      ]
      delete_access_table_arns = []
    }

    update_account = {
      name        = "UpdateAccount"
      description = "The role used by the WalterBackend API function to execute the UpdateAccount API. (${var.domain})"
      secrets = [
        module.secrets["Auth"].secret_name
      ]
      read_access_table_arns = [
        module.accounts_table.table_arn,
        module.sessions_table.table_arn,
        module.users_table.table_arn
      ]
      write_access_table_arns = [
        module.accounts_table.table_arn,
        module.sessions_table.table_arn,
        module.users_table.table_arn
      ]
      delete_access_table_arns = []
    }

    delete_account = {
      name        = "DeleteAccount"
      description = "The role used by the WalterBackend API function to execute the DeleteAccount API. (${var.domain})"
      secrets = [
        module.secrets["Auth"].secret_name
      ]
      read_access_table_arns = [
        module.accounts_table.table_arn,
        module.sessions_table.table_arn,
        module.users_table.table_arn
      ]
      write_access_table_arns = []
      delete_access_table_arns = [
        module.accounts_table.table_arn,
      ]
    }

    get_transactions = {
      name        = "GetTransactions"
      description = "The role used by the WalterBackend API function to execute the GetTransactions API. (${var.domain})"
      secrets = [
        module.secrets["Auth"].secret_name
      ]
      read_access_table_arns = [
        module.sessions_table.table_arn,
        module.accounts_table.table_arn,
        module.users_table.table_arn,
        module.holdings_table.table_arn,
        module.securities_table.table_arn,
        module.transactions_table.table_arn,
      ]
      write_access_table_arns  = []
      delete_access_table_arns = []
    }

    add_transaction = {
      name        = "AddTransaction"
      description = "The role used by the WalterBackend API function to execute the AddTransaction API. (${var.domain})"
      secrets = [
        module.secrets["Auth"].secret_name
      ]
      read_access_table_arns = [
        module.transactions_table.table_arn,
        module.sessions_table.table_arn,
        module.users_table.table_arn
      ]
      write_access_table_arns = [
        module.transactions_table.table_arn
      ]
      delete_access_table_arns = []
    }

    edit_transaction = {
      name        = "EditTransaction"
      description = "The role used by the WalterBackend API function to execute the EditTransaction API. (${var.domain})"
      secrets = [
        module.secrets["Auth"].secret_name
      ]
      read_access_table_arns = [
        module.transactions_table.table_arn,
        module.sessions_table.table_arn,
        module.users_table.table_arn
      ]
      write_access_table_arns = [
        module.transactions_table.table_arn,
      ]
      delete_access_table_arns = []
    }

    delete_transaction = {
      name        = "DeleteTransaction"
      description = "The role used by the WalterBackend API function to execute the DeleteTransaction API. (${var.domain})"
      secrets = [
        module.secrets["Auth"].secret_name
      ]
      read_access_table_arns = [
        module.transactions_table.table_arn,
        module.sessions_table.table_arn,
        module.users_table.table_arn
      ]
      write_access_table_arns = []
      delete_access_table_arns = [
        module.transactions_table.table_arn
      ]
    }

    create_link_token = {
      name        = "CreateLinkToken"
      description = "The role used by the WalterBackend API function to execute the CreateLinkToken API. (${var.domain})"
      secrets = [
        module.secrets["Auth"].secret_name,
        module.secrets["Plaid"].secret_name
      ]
      read_access_table_arns = [
        module.sessions_table.table_arn,
        module.users_table.table_arn
      ]
      write_access_table_arns = [
        module.sessions_table.table_arn,
        module.users_table.table_arn
      ]
      delete_access_table_arns = []
    }

    exchange_public_token = {
      name        = "ExchangePublicToken"
      description = "The role used by the WalterBackend API function to execute the ExchangePublicToken API. (${var.domain})"
      secrets = [
        module.secrets["Auth"].secret_name,
        module.secrets["Plaid"].secret_name
      ]
      read_access_table_arns = [
        module.sessions_table.table_arn,
        module.users_table.table_arn
      ]
      write_access_table_arns = [
        module.sessions_table.table_arn,
        module.users_table.table_arn
      ]
      delete_access_table_arns = [
        module.sessions_table.table_arn,
        module.users_table.table_arn
      ]
    }

    sync_transactions = {
      name        = "SyncTransactions"
      description = "The role used by the WalterBackend API function to execute the SyncTransactions API. (${var.domain})"
      secrets = [
        module.secrets["Auth"].secret_name,
        module.secrets["Plaid"].secret_name
      ]
      read_access_table_arns = [
        module.sessions_table.table_arn,
        module.users_table.table_arn,
        module.transactions_table.table_arn
      ]
      write_access_table_arns = [
        module.sessions_table.table_arn,
        module.users_table.table_arn,
        module.transactions_table.table_arn
      ]
      delete_access_table_arns = []
    }
  }
}

/*********************
 * WalterBackend API *
 *********************/

module "api_custom_domain" {
  source         = "./modules/api_gateway_custom_domain"
  api_id         = module.api.api_id
  base_domain    = local.BASE_DOMAIN
  domain         = var.domain
  hosted_zone_id = var.hosted_zone_id
  stage_name     = local.STAGE_NAME
}

module "api" {
  source                = "./modules/api_gateway"
  name                  = local.NAME
  description           = local.DESCRIPTION
  function_name         = module.functions["api"].function_name
  alias_name            = module.functions["api"].alias_name
  image_digest          = module.repositories["walter_backend"].image_digest
  stage_name            = local.STAGE_NAME
  log_retention_in_days = var.log_retention_in_days
}

resource "aws_api_gateway_resource" "auth" {
  rest_api_id = module.api.api_id
  parent_id   = module.api.root_resource_id
  path_part   = "auth"
}

resource "aws_api_gateway_resource" "plaid" {
  rest_api_id = module.api.api_id
  parent_id   = module.api.root_resource_id
  path_part   = "plaid"
}

module "resources" {
  for_each           = local.RESOURCES
  source             = "./modules/api_gateway_resource"
  rest_api_id        = module.api.api_id
  parent_resource_id = local.PARENT_TO_RESOURCE_ID[each.value.parent]
  path_part          = each.value.path
  enable_cors        = each.value.cors

  # add explicit dependencies to the required prerequisite resources
  depends_on = [
    aws_api_gateway_resource.auth,
    aws_api_gateway_resource.plaid
  ]
}

module "endpoints" {
  for_each          = local.ENDPOINTS
  source            = "./modules/api_gateway_endpoint"
  rest_api_id       = module.api.api_id
  resource_id       = module.resources[each.value.path].resource_id
  http_method       = each.value.method
  lambda_invoke_arn = module.functions["api"].invoke_arn
}

/***************************
 * WalterBackend API Roles *
 ***************************/

module "api_base_role" {
  source      = "./modules/iam_lambda_execution_role"
  name        = "WalterBackend-API-Role-${var.domain}"
  description = "The IAM role used by the WalterBackend API Lambda function to process API requests. (${var.domain})"
  policies = {
    assume_api_roles_policy = aws_iam_policy.api_assume_role_policy.arn
    api_kms_access_policy   = aws_iam_policy.api_kms_access_policy.arn
  }
}

resource "aws_iam_policy" "api_assume_role_policy" {
  name        = "WalterBackend-API-Base-Assume-Policy-${var.domain}"
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
      }
    ]
  })
}

resource "aws_iam_policy" "api_kms_access_policy" {
  name        = "WalterBackend-API-Base-KMS-Policy-${var.domain}"
  description = "The base IAM policy for the WalterBackend API function used to encrypt and decrypt with KMS keys."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "kms:*"
        ]
        Effect = "Allow"
        Resource = [
          module.functions["api"].kms_key_arn
        ]
      }
    ]
  })
}

module "api_roles" {
  source                     = "./modules/api_iam_roles"
  for_each                   = local.API_ROLES
  domain                     = var.domain
  name                       = each.value.name
  description                = each.value.description
  secret_names               = each.value.secrets
  read_table_access_arns     = each.value.read_access_table_arns
  write_table_access_arns    = each.value.write_access_table_arns
  delete_table_access_arns   = each.value.delete_access_table_arns
  api_base_role              = module.api_base_role.arn
  assume_api_role_principals = var.api_assume_role_additional_principals
}


