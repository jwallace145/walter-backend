locals {
  USERS_TABLE        = "Users-${var.domain}"
  SESSIONS_TABLE     = "Sessions-${var.domain}"
  ACCOUNTS_TABLE     = "Accounts-${var.domain}"
  TRANSACTIONS_TABLE = "Transactions-${var.domain}"
  SECURITIES_TABLE   = "Securities-${var.domain}"
  HOLDINGS_TABLE     = "Holdings-${var.domain}"

  USERS_EMAIL_INDEX                     = "Users-EmailIndex-${var.domain}"
  ACCOUNTS_PLAID_ACCOUNT_ID_INDEX       = "Accounts-PlaidAccountIdIndex-${var.domain}"
  ACCOUNTS_PLAID_ITEM_ID_INDEX          = "Accounts-PlaidItemIdIndex-${var.domain}"
  TRANSACTIONS_USER_DATE_RANGE_INDEX    = "Transactions-UserDateRangeIndex-${var.domain}"
  TRANSACTIONS_ACCOUNT_DATE_RANGE_INDEX = "Transactions-AccountDateRangeIndex-${var.domain}"
  SECURITIES_TICKER_INDEX               = "Securities-TickerIndex-${var.domain}"
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
      name     = local.USERS_EMAIL_INDEX
      hash_key = "email"
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
      name     = local.ACCOUNTS_PLAID_ACCOUNT_ID_INDEX
      hash_key = "plaid_account_id"
    },
    {
      name      = local.ACCOUNTS_PLAID_ITEM_ID_INDEX,
      hash_key  = "plaid_item_id",
      range_key = "plaid_account_id"
    }
  ]
}

# ------------------------------------------------------------------------------
# DynamoDB: Transactions Table
# ------------------------------------------------------------------------------
# Primary Key:
#   - Partition key: user_id
#   - Sort key:      transaction_id
#
# Purpose:
#   Models a one-to-many relationship between a user and their transactions.
#   Each transaction is uniquely identified by its transaction_id under a user.
#
# GSIs:
#   1. TRANSACTIONS_USER_DATE_RANGE_INDEX
#        - Keys: user_id + transaction_date
#        - Enables fast queries for all user transactions over a date range
#
#   2. TRANSACTIONS_ACCOUNT_DATE_RANGE_INDEX
#        - Keys: account_id + transaction_date
#        - Enables fast queries for all account transactions over a date range
#
# Design Rationale:
#   - Primary key (user_id + transaction_id) provides strong entity linkage.
#   - GSIs support the main access patterns:
#       * Get transactions by user over a date range (most common)
#       * Get transactions by account over a date range
#   - Optimized for serverless workloads with predictable key-based access.
# ------------------------------------------------------------------------------

module "transactions_table" {
  source = "./modules/dynamodb_table"

  name      = local.TRANSACTIONS_TABLE
  hash_key  = "user_id"
  range_key = "transaction_id"

  attributes = {
    user_id          = "S"
    account_id       = "S"
    transaction_id   = "S"
    transaction_date = "S"
  }

  global_secondary_indexes = [
    {
      name      = local.TRANSACTIONS_USER_DATE_RANGE_INDEX
      hash_key  = "user_id"
      range_key = "transaction_date"
    },
    {
      name      = local.TRANSACTIONS_ACCOUNT_DATE_RANGE_INDEX
      hash_key  = "account_id"
      range_key = "transaction_date"
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
      name     = local.SECURITIES_TICKER_INDEX
      hash_key = "ticker"
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