locals {
  NAME        = "WalterBackend-API"
  DESCRIPTION = "The API Gateway for all APIs served by WalterBackend."

  # all api resources for walter backend api defined here
  RESOURCES = {
    login    = { parent = "auth", path = "login", cors = true },
    refresh  = { parent = "auth", path = "refresh", cors = true },
    logout   = { parent = "auth", path = "logout", cors = true },
    users    = { parent = "root", path = "users", cors = true },
    accounts = { parent = "root", path = "accounts", cors = true }
  }

  # all endpoints served by walter backend are defined here
  ENDPOINTS = {

    # authentication endpoints
    login   = { parent = "auth", path = "login", method = "POST", cors = true },
    refresh = { parent = "auth", path = "refresh", method = "POST", cors = true },
    logout  = { parent = "auth", path = "logout", method = "POST", cors = true },

    # user endpoints
    get_user    = { parent = "root", path = "users", method = "GET", cors = true },
    create_user = { parent = "root", path = "users", method = "POST", cors = true },
    update_user = { parent = "root", path = "users", method = "PUT", cors = true },

    # account endpoints
    get_accounts   = { parent = "root", path = "accounts", method = "GET", cors = true },
    create_account = { parent = "root", path = "accounts", method = "POST", cors = true },
    update_account = { parent = "root", path = "accounts", method = "PUT", cors = true },
    delete_account = { parent = "root", path = "accounts", method = "DELETE", cors = true }
  }

  # used as a helper to get api gateway resource id from parent name
  PARENT_TO_RESOURCE_ID = {
    auth = aws_api_gateway_resource.auth.id,
    root = module.api.root_resource_id
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
  image_digest  = data.aws_ecr_image.walter_backend_image.image_digest
  stage_name    = "dev"
}

resource "aws_api_gateway_resource" "auth" {
  rest_api_id = module.api.api_id
  parent_id   = module.api.root_resource_id
  path_part   = "auth"
}

module "resources" {
  for_each           = local.RESOURCES
  source             = "./modules/api_gateway_resource"
  rest_api_id        = module.api.api_id
  parent_resource_id = local.PARENT_TO_RESOURCE_ID[each.value.parent]
  path_part          = each.value.path
  enable_cors        = each.value.cors
}

module "endpoints" {
  for_each          = local.ENDPOINTS
  source            = "./modules/api_gateway_endpoint"
  rest_api_id       = module.api.api_id
  resource_id       = module.resources[each.value.path].resource_id
  http_method       = each.value.method
  lambda_invoke_arn = module.functions["api"].invoke_arn
  enable_cors       = each.value.cors
}




