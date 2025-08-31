output "monitor_id" {
  description = "The ID of the created Datadog monitor"
  value       = datadog_monitor.lambda_function_timeout_monitor.id
}

output "monitor_name" {
  description = "The name of the created monitor"
  value       = datadog_monitor.lambda_function_timeout_monitor.name
}

output "monitor_url" {
  description = "The URL to view the monitor in Datadog"
  value       = "https://app.datadoghq.com/monitors/${datadog_monitor.lambda_function_timeout_monitor.id}"
}
