locals {
  ddb_tables = {
    users = {
      name      = local.users_table
      hash_key  = "user_id"
      range_key = null
      attributes = {
        user_id = "S"
        email   = "S"
      }

      gsis = [
        {
          name            = local.users_email_index.name
          hash_key        = "email"
          range_key       = null
          projection_type = "ALL"
        }
      ]

      ttl = null
    }

    sessions = {
      name      = local.sessions_table
      hash_key  = "user_id"
      range_key = "token_id"
      attributes = {
        user_id  = "S"
        token_id = "S"
      }

      gsis = []

      ttl = {
        attribute_name = "ttl"
        enabled        = true
      }
    }

    accounts = {
      name      = local.accounts_table
      hash_key  = "user_id"
      range_key = "account_id"
      attributes = {
        user_id    = "S"
        account_id = "S"
      }

      gsis = []

      ttl = null
    }

    transactions = {
      name      = local.transactions_table
      hash_key  = "account_id"
      range_key = "transaction_date"
      attributes = {
        user_id          = "S"
        account_id       = "S"
        transaction_date = "S"
      }

      gsis = [
        {
          name            = local.transactions_user_index.name
          hash_key        = "user_id"
          range_key       = "transaction_date"
          projection_type = "ALL"
        }
      ]

      ttl = null
    }

    securities = {
      name      = local.securities_table
      hash_key  = "security_id"
      range_key = null
      attributes = {
        security_id = "S"
        ticker      = "S"
      }

      gsis = [
        {
          name            = local.securities_ticker_index.name
          hash_key        = "ticker"
          range_key       = null
          projection_type = "ALL"
        }
      ]

      ttl = null
    }

    holdings = {
      name      = local.holdings_table
      hash_key  = "account_id"
      range_key = "security_id"
      attributes = {
        account_id  = "S"
        security_id = "S"
      }

      gsis = []

      ttl = null
    }
  }
}

resource "aws_dynamodb_table" "walterdb" {
  for_each = local.ddb_tables

  name         = each.value.name
  billing_mode = "PAY_PER_REQUEST"

  hash_key  = each.value.hash_key
  range_key = try(each.value.range_key, null)

  dynamic "attribute" {
    for_each = each.value.attributes
    content {
      name = attribute.key
      type = attribute.value
    }
  }

  dynamic "global_secondary_index" {
    for_each = try(each.value.gsis, [])
    content {
      name            = global_secondary_index.value.name
      hash_key        = global_secondary_index.value.hash_key
      range_key       = try(global_secondary_index.value.range_key, null)
      projection_type = try(global_secondary_index.value.projection_type, "ALL")
    }
  }

  dynamic "ttl" {
    for_each = try(each.value.ttl, null) == null ? [] : [each.value.ttl]
    iterator = t
    content {
      attribute_name = t.value["attribute_name"]
      enabled        = t.value["enabled"]
    }
  }
}
