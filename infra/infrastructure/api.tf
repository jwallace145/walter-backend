locals {
  NAME        = "WalterBackend-API"
  DESCRIPTION = "The API Gateway for all APIs served by WalterBackend."

  # all endpoints served by walter backend are defined here
  ENDPOINTS = {
    login    = { parent = "auth", path = "login", method = "POST", cors = true },
    refresh  = { parent = "auth", path = "refresh", method = "POST", cors = true },
    logout   = { parent = "auth", path = "logout", method = "POST", cors = true },
    get_user = { parent = "root", path = "users", method = "GET", cors = true },
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

module "endpoints" {
  for_each           = local.ENDPOINTS
  source             = "./modules/api_gateway_endpoint"
  rest_api_id        = module.api.api_id
  parent_resource_id = local.PARENT_TO_RESOURCE_ID[each.value.parent]
  path_part          = each.value.path
  http_method        = each.value.method
  lambda_invoke_arn  = module.functions["api"].invoke_arn
  enable_cors        = each.value.cors
}




