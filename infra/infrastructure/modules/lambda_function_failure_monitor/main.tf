resource "datadog_monitor" "lambda_function_failure_monitor" {
  name     = "WalterBackend (${var.domain}): ${var.component_name} Failure"
  priority = 1
  type     = "query alert"

  query = "max(last_15m):max:${lower(var.component_name)}.failure{domain:${var.domain}} == 1"

  monitor_thresholds {
    critical = 1
  }

  message = <<EOT
# WalterBackend (${var.domain}): ${var.component_name} Failure!

The `${var.function_name}` Lambda function detected a failure! Investigate the function's metris and determine the root cause.

### Helpful Links

* [walter-frontend-v2](https://github.com/jwallace145/walter-frontend-v2)
* [walter-backend](https://github.com/jwallace145/walter-backend)
EOT

  on_missing_data     = "show_and_notify_no_data"
  require_full_window = false # Datadog strongly recommends not requiring the full window for sparse metrics
  include_tags        = false
  tags                = ["team:walteraidevelopers"]
}
