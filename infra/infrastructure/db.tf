locals {
  USERS_TABLE        = "Users-${var.domain}"
  SESSIONS_TABLE     = "Sessions-${var.domain}"
  ACCOUNTS_TABLE     = "Accounts-${var.domain}"
  TRANSACTIONS_TABLE = "Transactions-${var.domain}"
  SECURITIES_TABLE   = "Securities-${var.domain}"
  HOLDINGS_TABLE     = "Holdings-${var.domain}"

  USERS_EMAIL_INDEX               = "Users-EmailIndex-${var.domain}"
  ACCOUNTS_PLAID_ACCOUNT_ID_INDEX = "Accounts-PlaidAccountIdIndex-${var.domain}"
  ACCOUNTS_PLAID_ITEM_ID_INDEX    = "Accounts-PlaidItemIdIndex-${var.domain}"
  TRANSACTIONS_USER_INDEX         = "Transactions-UserIndex-${var.domain}"
  SECURITIES_TICKER_INDEX         = "Securities-TickerIndex-${var.domain}"
}

/*******************
 * WalterDB Tables *
 *******************/

module "users_table" {
  source = "./modules/dynamodb_table"

  name     = local.USERS_TABLE
  hash_key = "user_id"

  attributes = {
    user_id = "S"
    email   = "S"
  }

  global_secondary_indexes = [
    {
      name            = local.USERS_EMAIL_INDEX
      hash_key        = "email"
      projection_type = "ALL"
    }
  ]
}

module "sessions_table" {
  source = "./modules/dynamodb_table"

  name      = local.SESSIONS_TABLE
  hash_key  = "user_id"
  range_key = "token_id"

  attributes = {
    user_id  = "S"
    token_id = "S"
  }

  ttl = {
    attribute_name = "ttl"
    enabled        = true
  }
}

module "accounts_table" {
  source = "./modules/dynamodb_table"

  name      = local.ACCOUNTS_TABLE
  hash_key  = "user_id"
  range_key = "account_id"

  attributes = {
    user_id          = "S"
    account_id       = "S"
    plaid_account_id = "S"
    plaid_item_id    = "S"
  }

  global_secondary_indexes = [
    {
      name            = local.ACCOUNTS_PLAID_ACCOUNT_ID_INDEX
      hash_key        = "plaid_account_id"
      projection_type = "ALL"
    },
    {
      name            = local.ACCOUNTS_PLAID_ITEM_ID_INDEX,
      hash_key        = "plaid_item_id",
      range_key       = "plaid_account_id"
      projection_type = "ALL"
    }
  ]
}

module "transactions_table" {
  source = "./modules/dynamodb_table"

  name      = local.TRANSACTIONS_TABLE
  hash_key  = "account_id"
  range_key = "transaction_date"

  attributes = {
    user_id          = "S"
    account_id       = "S"
    transaction_date = "S"
  }

  global_secondary_indexes = [
    {
      name            = local.TRANSACTIONS_USER_INDEX
      hash_key        = "user_id"
      range_key       = "transaction_date"
      projection_type = "ALL"
    }
  ]
}

module "securities_table" {
  source = "./modules/dynamodb_table"

  name     = local.SECURITIES_TABLE
  hash_key = "security_id"

  attributes = {
    security_id = "S"
    ticker      = "S"
  }

  global_secondary_indexes = [
    {
      name            = local.SECURITIES_TICKER_INDEX
      hash_key        = "ticker"
      projection_type = "ALL"
    }
  ]
}

module "holdings_table" {
  source = "./modules/dynamodb_table"

  name      = local.HOLDINGS_TABLE
  hash_key  = "account_id"
  range_key = "security_id"

  attributes = {
    account_id  = "S"
    security_id = "S"
  }
}