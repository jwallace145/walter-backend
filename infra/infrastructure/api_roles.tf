locals {
  API_ROLES = {
    login = {
      name        = "Login"
      description = "The role used by the WalterBackend API function to execute the Login API. (${var.domain})"
      secrets = [
        module.secrets["Auth"].secret_name
      ]
      tables = [
        module.users_table.table_name
      ]
    }

    logout = {
      name        = "Logout"
      description = "The role used by the WalterBackend API function to execute the Logout API. (${var.domain})"
      secrets = [
        module.secrets["Auth"].secret_name
      ]
      tables = [
        module.users_table.table_name,
        module.sessions_table.table_name
      ]
    }
  }
}

/***************************
 * WalterBackend API Roles *
 ***************************/

module "api_roles" {
  source       = "./modules/api_iam_roles"
  for_each     = local.API_ROLES
  domain       = var.domain
  name         = each.value.name
  description  = each.value.description
  secret_names = each.value.secrets
  table_names  = each.value.tables
}
