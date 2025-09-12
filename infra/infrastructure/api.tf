locals {
  NAME        = "WalterBackend-API"
  DESCRIPTION = "The API Gateway for all APIs served by WalterBackend."

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
    refresh = { parent = "auth", path = "refresh", method = "POST" },
    logout  = { parent = "auth", path = "logout", method = "POST" },

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
}

/*********************
 * WalterBackend API *
 *********************/

module "api" {
  source        = "./modules/api_gateway"
  name          = local.NAME
  description   = local.DESCRIPTION
  function_name = module.functions["api"].function_name
  image_digest  = "sha256:951814ece918d9b1dace8203e041e86342059720f775e7e5f42f82545ed067d8"
  stage_name    = "dev"
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




