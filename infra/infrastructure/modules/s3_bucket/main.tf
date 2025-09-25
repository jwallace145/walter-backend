resource "aws_s3_bucket" "bucket" {
  bucket = "${var.name_prefix}-${var.domain}"
}

resource "aws_s3_bucket_versioning" "bucket_versioning" {
  bucket = aws_s3_bucket.bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_ownership_controls" "bucket_ownership_controls" {
  bucket = aws_s3_bucket.bucket.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "bucket_acl" {
  depends_on = [aws_s3_bucket_ownership_controls.bucket_ownership_controls]

  bucket = aws_s3_bucket.bucket.id
  acl    = "private"
}

resource "aws_s3_bucket_policy" "bucket_policy" {
  bucket = aws_s3_bucket.bucket.id
  policy = data.aws_iam_policy_document.bucket_policy_document.json
}

data "aws_iam_policy_document" "bucket_policy_document" {
  dynamic "statement" {
    for_each = var.read_access_principals
    content {
      sid    = "ReadAccess${replace(replace(statement.value.prefix, "/", ""), "*", "Wildcard")}${statement.key}"
      effect = "Allow"

      principals {
        type        = "AWS"
        identifiers = statement.value.principals
      }

      actions = [
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:GetObjectAcl",
        "s3:GetObjectVersionAcl"
      ]

      resources = [
        "${aws_s3_bucket.bucket.arn}/${statement.value.prefix}"
      ]
    }
  }

  dynamic "statement" {
    for_each = var.read_access_principals
    content {
      sid    = "ListAccess${replace(replace(statement.value.prefix, "/", ""), "*", "Wildcard")}${statement.key}"
      effect = "Allow"

      principals {
        type        = "AWS"
        identifiers = statement.value.principals
      }

      actions = [
        "s3:ListBucket"
      ]

      resources = [
        aws_s3_bucket.bucket.arn
      ]

      condition {
        test     = "StringLike"
        variable = "s3:prefix"
        values   = ["${statement.value.prefix}"]
      }
    }
  }

  dynamic "statement" {
    for_each = var.write_access_principals
    content {
      sid    = "WriteAccess${replace(replace(statement.value.prefix, "/", ""), "*", "Wildcard")}${statement.key}"
      effect = "Allow"

      principals {
        type        = "AWS"
        identifiers = statement.value.principals
      }

      actions = [
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:GetObjectAcl",
        "s3:GetObjectVersionAcl"
      ]

      resources = [
        "${aws_s3_bucket.bucket.arn}/${statement.value.prefix}"
      ]
    }
  }

  dynamic "statement" {
    for_each = var.write_access_principals
    content {
      sid    = "WriteListAccess${replace(replace(statement.value.prefix, "/", ""), "*", "Wildcard")}${statement.key}"
      effect = "Allow"

      principals {
        type        = "AWS"
        identifiers = statement.value.principals
      }

      actions = [
        "s3:ListBucket"
      ]

      resources = [
        aws_s3_bucket.bucket.arn
      ]

      condition {
        test     = "StringLike"
        variable = "s3:prefix"
        values   = ["${statement.value.prefix}"]
      }
    }
  }

  dynamic "statement" {
    for_each = var.delete_access_principals
    content {
      sid    = "DeleteAccess${replace(replace(statement.value.prefix, "/", ""), "*", "Wildcard")}${statement.key}"
      effect = "Allow"

      principals {
        type        = "AWS"
        identifiers = statement.value.principals
      }

      actions = [
        "s3:DeleteObject",
        "s3:DeleteObjectVersion",
        "s3:GetObject",
        "s3:GetObjectVersion"
      ]

      resources = [
        "${aws_s3_bucket.bucket.arn}/${statement.value.prefix}"
      ]
    }
  }

  dynamic "statement" {
    for_each = var.delete_access_principals
    content {
      sid    = "DeleteListAccess${replace(replace(statement.value.prefix, "/", ""), "*", "Wildcard")}${statement.key}"
      effect = "Allow"

      principals {
        type        = "AWS"
        identifiers = statement.value.principals
      }

      actions = [
        "s3:ListBucket"
      ]

      resources = [
        aws_s3_bucket.bucket.arn
      ]

      condition {
        test     = "StringLike"
        variable = "s3:prefix"
        values   = ["${statement.value.prefix}"]
      }
    }
  }

  dynamic "statement" {
    for_each = var.cloudfront_distribution_arns != null ? var.cloudfront_distribution_arns : []
    content {
      sid    = "CloudFrontReadAccess${replace(statement.value, ":", "_")}"
      effect = "Allow"

      principals {
        type        = "Service"
        identifiers = ["cloudfront.amazonaws.com"]
      }

      actions = [
        "s3:GetObject",
        "s3:GetObjectVersion"
      ]

      resources = [
        "${aws_s3_bucket.bucket.arn}/public/*"
      ]

      condition {
        test     = "StringEquals"
        variable = "AWS:SourceArn"
        values   = [statement.value]
      }
    }
  }
}