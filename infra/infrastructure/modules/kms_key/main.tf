locals {
  KMS_KEY_ALIAS_NAME = "WalterBackend-${var.name}-Key-${var.domain}"
}

resource "aws_kms_key" "key" {
  description             = var.description
  enable_key_rotation     = false
  deletion_window_in_days = 7
  policy = jsonencode({
    Version = "2012-10-17"
    Id      = "key-default-1"
    Statement = [
      {
        Sid    = "AllowKMSAccess"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${var.account_id}:root"
        },
        Action   = "kms:*"
        Resource = "*"
      }
    ]
  })
}

resource "aws_kms_alias" "alias" {
  name          = "alias/${local.KMS_KEY_ALIAS_NAME}"
  target_key_id = aws_kms_key.key.id
}
