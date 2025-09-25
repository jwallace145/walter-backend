/***********************
 * WalterBackend (dev) *
 ***********************/

# WalterAI dev account details
account_id        = "010526272437"
region            = "us-east-1"
availability_zone = "us-east-1a"
domain            = "dev"

# WalterBackend application version
walter_backend_version = "0.0.0"

# The logging level, can set to debug for more verbose logs
log_level = "DEBUG"

# The number of days to retain application logs before deletion
log_retention_in_days = 7

# walterai.dev Route53 hosted zone ID
hosted_zone_id = "Z06872281VCZDG3SK2QXB"

# WalterBackend Network settings
# The WalterBackend functions create ENIs in the private subnets assigned to private IPs
# that serve requests, for higher environments, a larger address should be used
network_cidr        = "10.0.0.0/27"  # 32 IPs total
public_subnet_cidr  = "10.0.0.0/28"  # 16 public IPs (AWS reserves 5 IPs) = 11 usable IPs
private_subnet_cidr = "10.0.0.16/28" # 16 private IPs (AWS reserves 5 IPs) = 11 usable IPs

# WalterBackend API settings
api_timeout_seconds                   = 15
api_lambda_memory_mb                  = 1024
api_provisioned_concurrent_executions = 0
api_assume_role_additional_principals = ["arn:aws:iam::010526272437:user/WalterAIDeveloper"]

# WalterBackend Canary settings
canary_timeout_seconds                   = 30
canary_lambda_memory_mb                  = 1024
canary_provisioned_concurrent_executions = 0
canary_assume_role_additional_principals = ["arn:aws:iam::010526272437:user/WalterAIDeveloper"]

# WalterBackend Workflow Settings
workflow_timeout_seconds                   = 15
workflow_lambda_memory_mb                  = 1024
workflow_provisioned_concurrent_executions = 0
workflow_assume_role_additional_principals = ["arn:aws:iam::010526272437:user/WalterAIDeveloper"]

# SyncUserTransactions Workflow Settings
sync_transactions_max_concurrency    = 2
sync_transactions_max_retry_attempts = 1

# WalterBackend CloudFront CDN Settings
cdn_bucket_access_additional_principals = ["arn:aws:iam::010526272437:user/WalterAIDeveloper"]
