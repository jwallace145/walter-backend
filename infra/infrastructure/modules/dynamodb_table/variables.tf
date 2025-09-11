variable "name" {
  description = "Name of the DynamoDB table"
  type        = string
}

variable "hash_key" {
  description = "Hash key (partition key) for the table"
  type        = string
}

variable "range_key" {
  description = "Range key (sort key) for the table"
  type        = string
  default     = null
}

variable "attributes" {
  description = "Map of attribute names to their types (S, N, B)"
  type        = map(string)
}

variable "global_secondary_indexes" {
  description = "List of global secondary index configurations"
  type = list(object({
    name            = string
    hash_key        = string
    range_key       = optional(string)
    projection_type = optional(string, "ALL")
  }))
  default = []
}

variable "ttl" {
  description = "TTL configuration"
  type = object({
    attribute_name = string
    enabled        = bool
  })
  default = null
}

variable "billing_mode" {
  description = "Billing mode for the table"
  type        = string
  default     = "PAY_PER_REQUEST"
}