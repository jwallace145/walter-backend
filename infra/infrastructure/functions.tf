locals {
  FUNCTIONS = {
    api = {
      name                              = "WalterBackend-API-${var.domain}"
      component                         = "API"
      description                       = "The entrypoint function for all APIs included in WalterBackend (v${var.walter_backend_version}-${var.domain})."
      function_version                  = var.api_function_version
      role_arn                          = module.api_role.arn
      timeout                           = var.api_timeout_seconds
      memory_size                       = var.api_lambda_memory_mb
      lambda_handler                    = "walter.api_entrypoint"
      provisioned_concurrent_executions = var.api_provisioned_concurrent_executions
    },
    canary = {
      name                              = "WalterBackend-Canary-${var.domain}"
      component                         = "Canary"
      description                       = "The single entrypoint for all API canaries in WalterBackend (v${var.walter_backend_version}-${var.domain})."
      function_version                  = var.canary_function_version
      role_arn                          = module.canary_role.arn
      timeout                           = var.canary_timeout_seconds
      memory_size                       = var.canary_lambda_memory_mb
      lambda_handler                    = "walter.canaries_entrypoint"
      provisioned_concurrent_executions = var.canary_provisioned_concurrent_executions
    },
    workflow = {
      name                              = "WalterBackend-Workflow-${var.domain}"
      component                         = "Workflow"
      description                       = "The entrypoint function for all asynchronous workflows in WalterBackend (v${var.walter_backend_version}-${var.domain})."
      function_version                  = var.workflow_function_version
      role_arn                          = module.workflow_role.arn
      timeout                           = var.workflow_timeout_seconds
      memory_size                       = var.workflow_lambda_memory_mb
      lambda_handler                    = "walter.workflows_entrypoint"
      provisioned_concurrent_executions = var.workflow_provisioned_concurrent_executions
    }
  }

  SCHEDULES = {
    canary = {
      name                = "WalterBackend-Canary-Schedule-${var.domain}"
      description         = "The schedule to invoke the WalterBackend canary (${var.domain})."
      function_arn        = module.functions["canary"].function_arn
      schedule_expression = "rate(5 minutes)"
      input               = null
    },
    update_prices = {
      name                = "WalterBackend-UpdatePrices-Schedule-${var.domain}"
      description         = "The schedule to invoke the UpdatePrices workflow (${var.domain})."
      function_arn        = module.functions["workflow"].function_arn
      schedule_expression = "rate(5 minutes)"
      input = jsonencode({
        workflow_name = "UpdateSecurityPrices"
      })
    }
  }

  FUNCTION_QUEUES = {
    sync_transactions = {
      function_name       = local.FUNCTIONS.workflow.name,
      queue_arn           = module.queues["sync_transactions"].queue_arn,
      maximum_concurrency = var.sync_transactions_max_concurrency
      max_retry_attempts  = var.sync_transactions_max_retry_attempts
    }
  }
}

/***************************
 * WalterBackend Functions *
 ***************************/

module "functions" {
  for_each                          = local.FUNCTIONS
  source                            = "./modules/lamdba_function"
  function_name                     = each.value.name
  description                       = each.value.description
  image_uri                         = "010526272437.dkr.ecr.us-east-1.amazonaws.com/walter-backend-dev:0.0.0"
  role_arn                          = each.value.role_arn
  timeout                           = each.value.timeout
  memory_size                       = each.value.memory_size
  lambda_handler                    = each.value.lambda_handler
  log_level                         = var.log_level
  domain                            = var.domain
  publish                           = true
  log_retention_in_days             = var.log_retention_in_days
  datadog_api_key                   = var.datadog_api_key
  datadog_site                      = var.datadog_site
  provisioned_concurrent_executions = each.value.provisioned_concurrent_executions
  alias_name                        = "release"
  function_version                  = each.value.function_version
}

/************************************
 * WalterBackend Function Schedules *
 ************************************/

module "schedules" {
  for_each            = local.SCHEDULES
  source              = "./modules/lambda_schedule"
  name                = each.value.name
  description         = each.value.description
  lambda_function_arn = each.value.function_arn
  schedule_expression = each.value.schedule_expression
  input               = each.value.input
}

/*********************************
 * WalterBackend Function Queues *
 *********************************/

module "function_queues" {
  source              = "./modules/lambda_function_queue"
  for_each            = local.FUNCTION_QUEUES
  function_name       = each.value.function_name
  queue_arn           = each.value.queue_arn
  maximum_concurrency = each.value.maximum_concurrency
}

/*************************************
 * WalterBackend Function Monitoring *
 *************************************/

module "failure_monitors" {
  for_each       = local.FUNCTIONS
  source         = "./modules/lambda_function_failure_monitor"
  component_name = each.value.component
  domain         = var.domain
  function_name  = each.value.name
}

module "timeout_monitors" {
  for_each       = local.FUNCTIONS
  source         = "./modules/lambda_function_timeout_monitor"
  component_name = each.value.component
  domain         = var.domain
  function_name  = each.value.name
  timeout        = each.value.timeout
}

module "memory_monitors" {
  for_each           = local.FUNCTIONS
  source             = "./modules/lambda_function_memory_monitor"
  component_name     = each.value.component
  domain             = var.domain
  function_memory_mb = each.value.memory_size
  function_name      = each.value.name
}
