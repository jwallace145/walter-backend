locals {
  QUEUES = {
    sync_transactions = { name = "SyncTransactions", max_retries = 3 }
  }
}

/**********
 * QUEUES *
 **********/

module "queues" {
  source                           = "./modules/sqs_queue"
  for_each                         = local.QUEUES
  service                          = local.SERVICE_NAME
  name                             = each.value.name
  domain                           = var.domain
  redrive_policy_max_receive_count = each.value.max_retries
}
