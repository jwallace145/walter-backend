/***********************
 * WalterBackend (dev) *
 ***********************/

# WalterBackend application domain
domain = "dev"

# The logging level, can set to debug for more verbose logs
log_level = "INFO"

# WalterBackend development image
image_uri = "010526272437.dkr.ecr.us-east-1.amazonaws.com/walter-backend:latest"

# WalterBackend API settings
api_timeout_seconds  = 15
api_lambda_memory_mb = 1024

# WalterBackend Canary settings
canary_timeout_seconds  = 30
canary_lambda_memory_mb = 1024

# WalterBackend Workflow Settings
workflow_timeout_seconds  = 15
workflow_lambda_memory_mb = 1024

