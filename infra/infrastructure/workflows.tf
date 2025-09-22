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
  source             = "./modules/base_function_role"
  account_id         = var.account_id
  domain             = var.domain
  component          = "Workflow"
  description        = "The IAM role used by the WalterBackend Workflow function to assume execution roles. (${var.domain})"
  assumable_entities = [for role in local.WORKFLOW_ROLES : role.name]
  kms_key_arns       = [module.env_vars_key.arn]
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

