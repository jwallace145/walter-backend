data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}
data "aws_region" "current" {}

locals {

  # TODO: Finish migrating the following resources

  walterapi_role = "WalterAPIRole-${var.domain}"

  /************************
   AWS Account Information
   ************************/

  aws_account_id = data.aws_caller_identity.current.account_id
  aws_partition  = data.aws_partition.current.partition
  aws_region     = data.aws_region.current.name

  /*************************************
   WalterDB DynamoDB Tables and Indexes
  **************************************/

  users_table        = "Users-${var.domain}"
  sessions_table     = "Sessions-${var.domain}"
  accounts_table     = "Accounts-${var.domain}"
  transactions_table = "Transactions-${var.domain}"
  securities_table   = "Securities-${var.domain}"
  holdings_table     = "Holdings-${var.domain}"

  users_email_index = {
    table = local.users_table
    name  = "Users-EmailIndex-${var.domain}"
  }
  transactions_user_index = {
    table = local.transactions_table
    name  = "Transactions-UserIndex-${var.domain}"
  }
  securities_ticker_index = {
    table = local.securities_table
    name  = "Securities-TickerIndex-${var.domain}"
  }

  walterdb_tables = [
    local.users_table,
    local.sessions_table,
    local.accounts_table,
    local.transactions_table,
    local.securities_table,
    local.holdings_table
  ]

  walterdb_indexes = [
    local.users_email_index,
    local.transactions_user_index,
    local.securities_ticker_index
  ]

  /**********************
   WalterBackend Secrets
   **********************/

  auth_secrets           = "WalterAuthSecrets-dev"
  polygon_api_key_secret = "PolygonAPIKey"
  datadog_api_key_secret = "WalterBackendDatadogAPIKey"
  stripe_api_key_secret  = "StripeTestSecretKey"
  plaid_api_key_secret   = "PlaidSandboxCredentials"

  walterbackend_secrets = [
    local.auth_secrets,
    local.polygon_api_key_secret,
    local.datadog_api_key_secret,
    local.stripe_api_key_secret,
    local.plaid_api_key_secret
  ]



}