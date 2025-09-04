locals {
  WARNING_THRESHOLD  = floor(0.7 * var.timeout)
  CRITICAL_THRESHOLD = floor(0.9 * var.timeout)
}

resource "datadog_monitor" "lambda_function_timeout_monitor" {
  name     = "WalterBackend (${var.domain}): ${var.component_name} High Duration"
  priority = 1
  type     = "query alert"

  query = "max(last_15m):max:aws.lambda.enhanced.duration{functionname:${lower(var.function_name)}} >= ${local.CRITICAL_THRESHOLD}"

  monitor_thresholds {
    warning  = local.WARNING_THRESHOLD
    critical = local.CRITICAL_THRESHOLD
  }

  message = <<EOT
# WalterBackend (${var.domain}): ${var.component_name} High Duration!

The `${var.function_name}` Lambda function is near its max timeout in execution duration!

Determine the root cause of the increased function duration. Consider bumping the max timeout of the function if increased duration is justified.

### Helpful Links

* [walter-frontend-v2](https://github.com/jwallace145/walter-frontend-v2)
* [walter-backend](https://github.com/jwallace145/walter-backend)
EOT

  on_missing_data     = "show_no_data"
  require_full_window = false # Datadog strongly recommends not requiring the full window for sparse metrics
  include_tags        = false
  tags                = ["team:walteraidevelopers", "domain:${var.domain}", "component:${lower(var.component_name)}"]
}
