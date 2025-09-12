/***********************
 * WalterBackend (dev) *
 ***********************/

# WalterAI dev account details
account_id = "010526272437"
region     = "us-east-1"
domain     = "dev"

# WalterBackend application version
walter_backend_version = "0.0.0"

# The logging level, can set to debug for more verbose logs
log_level = "INFO"

# The number of days to retain application logs before deletion
log_retention_in_days = 14

# WalterBackend API settings
api_timeout_seconds                   = 15
api_lambda_memory_mb                  = 1024
api_provisioned_concurrent_executions = 1

# WalterBackend Canary settings
canary_timeout_seconds                   = 30
canary_lambda_memory_mb                  = 1024
canary_provisioned_concurrent_executions = 1

# WalterBackend Workflow Settings
workflow_timeout_seconds                   = 15
workflow_lambda_memory_mb                  = 1024
workflow_provisioned_concurrent_executions = 1

# SyncUserTransactions Workflow Settings
sync_transactions_max_concurrency    = 2
sync_transactions_max_retry_attempts = 1
