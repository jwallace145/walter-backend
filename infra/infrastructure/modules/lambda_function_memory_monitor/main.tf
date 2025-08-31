locals {
  WARNING_THRESHOLD  = floor(0.8 * var.function_memory_mb)
  CRITICAL_THRESHOLD = floor(0.9 * var.function_memory_mb)
}

resource "datadog_monitor" "lambda_function_memory_monitor" {
  name     = "WalterBackend (${var.domain}): ${var.component_name} High Memory Usage"
  priority = 1
  type     = "query alert"

  query = "avg(last_15m):avg:aws.lambda.enhanced.max_memory_used{functionname:${lower(var.function_name)}} >= ${local.CRITICAL_THRESHOLD}"

  monitor_thresholds {
    warning  = local.WARNING_THRESHOLD
    critical = local.CRITICAL_THRESHOLD
  }

  message = <<EOT
# WalterBackend (${var.domain}): ${var.component_name} High Memory Usage!

The `${var.function_name}` Lambda function is near its memory limits! This can cause unexpected errors due to memory constraints.

Investigate the function logs and root cause the high memory usage. Increase the memory allocated to the function if necessary.

### Helpful Links

* [walter-frontend-v2](https://github.com/jwallace145/walter-frontend-v2)
* [walter-backend](https://github.com/jwallace145/walter-backend)
EOT

  on_missing_data     = "show_no_data"
  require_full_window = false # Datadog strongly recommends not requiring the full window for sparse metrics
  include_tags        = false
  tags                = ["team:walteraidevelopers"]
}
