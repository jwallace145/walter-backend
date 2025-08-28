locals {
  FUNCTIONS = {
    api = {
      name           = "WalterBackend-API-${var.domain}"
      description    = "The entrypoint function for all APIs included in WalterBackend (${var.domain})."
      role_arn       = module.api_role.arn
      timeout        = var.api_timeout_seconds
      memory_size    = var.api_lambda_memory_mb
      lambda_handler = "walter.api_entrypoint"
    },
    canary = {
      name           = "WalterBackend-Canary-${var.domain}"
      description    = "The single entrypoint for all API canaries in WalterBackend (${var.domain})."
      role_arn       = module.canary_role.arn
      timeout        = var.canary_timeout_seconds
      memory_size    = var.canary_lambda_memory_mb
      lambda_handler = "walter.canaries_entrypoint"
    },
    workflow = {
      name           = "WalterBackend-Workflow-${var.domain}"
      description    = "The entrypoint function for all asynchronous workflows in WalterBackend (${var.domain})."
      role_arn       = module.workflow_role.arn
      timeout        = var.workflow_timeout_seconds
      memory_size    = var.workflow_lambda_memory_mb
      lambda_handler = "walter.workflows_entrypoint"
    }
  }
}

/***************************
 * WalterBackend Functions *
 ***************************/

module "functions" {
  for_each       = local.FUNCTIONS
  source         = "./modules/lamdba_function"
  function_name  = each.value.name
  description    = each.value.description
  image_uri      = var.image_uri
  role_arn       = each.value.role_arn
  timeout        = each.value.timeout
  memory_size    = each.value.memory_size
  lambda_handler = each.value.lambda_handler
  log_level      = var.log_level
  domain         = var.domain
  publish        = true
}
