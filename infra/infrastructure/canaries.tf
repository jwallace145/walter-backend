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

module "canary_role" {
  source             = "./modules/base_function_role"
  account_id         = var.account_id
  domain             = var.domain
  component          = "Canary"
  description        = "The IAM role used by the WalterBackend Canary function to assume execution roles to test API health. (${var.domain})"
  assumable_entities = [for role in local.CANARY_ROLES : role.name]
  kms_key_arns       = [module.env_vars_key.arn]
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


