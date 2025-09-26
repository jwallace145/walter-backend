locals {
  SECRETS = {
    Auth = {
      ACCESS_TOKEN_SECRET_KEY  = var.access_token_secret_key
      REFRESH_TOKEN_SECRET_KEY = var.refresh_token_secret_key
    }
    Datadog = {
      DATADOG_API_KEY = var.datadog_api_key
      DATADOG_APP_KEY = var.datadog_app_key
      DATADOG_SITE    = var.datadog_site
    }
    Plaid = {
      PLAID_CLIENT_ID  = var.plaid_client_id
      PLAID_SECRET_KEY = var.plaid_secret
    }
    Polygon = {
      POLYGON_API_KEY = var.polygon_api_key
    }
    Stripe = {
      STRIPE_SECRET_KEY = var.stripe_secret_key
    }
    WalterBackendAPIKey = {
      WALTER_BACKEND_API_KEY = var.walter_backend_api_key
    }
  }

  DESCRIPTIONS = {
    Auth                = "The secret keys used for authentication by WalterBackend to sign and verify API requests. (${var.domain})"
    Datadog             = "The Datadog secret keys used by WalterBackend to emit metrics and send logs to Datadog for dashboards and monitoring. (${var.domain})"
    Plaid               = "The Plaid client ID and secret used by WalterBackend to authenticate with Plaid. (${var.domain})"
    Polygon             = "The Polygon API key used to make requests to Polygon. (${var.domain})"
    Stripe              = "The secret key used to interact with Stripe for customer billing. (${var.domain})"
    WalterBackendAPIKey = "The API key used to make calls to the WalterBackend API. (${var.domain})"
  }
}

/*************************
 * WalterBackend Secrets *
 *************************/

module "secrets" {
  for_each           = local.SECRETS
  source             = "./modules/secrets_manager"
  secret_name        = "WalterBackend-${each.key}-Secrets-${var.domain}"
  secret_description = local.DESCRIPTIONS[each.key]
  secret_data        = each.value
}
