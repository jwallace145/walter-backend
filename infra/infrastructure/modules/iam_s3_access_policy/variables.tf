variable "policy_name" {
  description = "Optional name for the IAM policy. If not provided, a default name will be used."
  type        = string
}

variable "read_access_bucket_prefixes" {
  description = "List of S3 bucket prefixes to grant READ access to (object read and bucket list)."
  type        = list(string)
}

variable "write_access_bucket_prefixes" {
  description = "List of S3 bucket prefixes to grant WRITE access to (object put)."
  type        = list(string)
}

variable "delete_access_bucket_prefixes" {
  description = "List of S3 bucket prefixes to grant DELETE access to (object delete)."
  type        = list(string)
}
