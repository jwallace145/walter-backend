locals {
  # Provided inputs are S3 object prefix ARNs, e.g., arn:aws:s3:::my-bucket/path/*
  read_prefix_arns   = var.read_access_bucket_prefixes
  write_prefix_arns  = var.write_access_bucket_prefixes
  delete_prefix_arns = var.delete_access_bucket_prefixes

  # Extract bucket names from ARN and derive bucket ARNs for ListBucket
  read_bucket_names = distinct([
    for arn in local.read_prefix_arns : split("/", replace(arn, "arn:aws:s3:::", ""))[0]
  ])
  read_bucket_arns = [for b in local.read_bucket_names : "arn:aws:s3:::${b}"]

  # Derive the key prefixes (without bucket and without trailing *) for ListBucket condition
  read_key_prefixes = [
    for arn in local.read_prefix_arns :
    replace(
      join("/", slice(
        split("/", replace(arn, "arn:aws:s3:::", "")),
        1,
        length(split("/", replace(arn, "arn:aws:s3:::", "")))
      )),
      "*",
      ""
    )
  ]
}

resource "aws_iam_policy" "this" {
  name   = var.policy_name
  policy = data.aws_iam_policy_document.this.json
}

data "aws_iam_policy_document" "this" {
  # READ access: list bucket (scoped by key prefix) and get objects
  dynamic "statement" {
    for_each = length(local.read_prefix_arns) > 0 ? [1] : []
    content {
      sid = "S3ReadBucketAccess"

      actions = [
        "s3:ListBucket"
      ]

      resources = local.read_bucket_arns

      condition {
        test     = "StringLike"
        variable = "s3:prefix"
        values   = local.read_key_prefixes
      }
    }
  }

  dynamic "statement" {
    for_each = length(local.read_prefix_arns) > 0 ? [1] : []
    content {
      sid = "S3ReadObjectAccess"

      actions = [
        "s3:GetObject",
        "s3:GetObjectVersion"
      ]

      resources = local.read_prefix_arns
    }
  }

  # WRITE access: put objects
  dynamic "statement" {
    for_each = length(local.write_prefix_arns) > 0 ? [1] : []
    content {
      sid = "S3WriteObjectAccess"

      actions = [
        "s3:PutObject"
      ]

      resources = local.write_prefix_arns
    }
  }

  # DELETE access: delete objects
  dynamic "statement" {
    for_each = length(local.delete_prefix_arns) > 0 ? [1] : []
    content {
      sid = "S3DeleteObjectAccess"

      actions = [
        "s3:DeleteObject",
        "s3:DeleteObjectVersion"
      ]

      resources = local.delete_prefix_arns
    }
  }
}