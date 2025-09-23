locals {
  BASE_FUNCTION_ROLE_NAME       = "WalterBackend-${var.component}-Base-Role-${var.domain}"
  BASE_FUNCTION_STS_POLICY_NAME = "WalterBackend-${var.component}-Base-STS-Policy-${var.domain}"
  BASE_FUNCTION_KMS_POLICY_NAME = "WalterBackend-${var.component}-Base-KMS-Policy-${var.domain}"
  BASE_FUNCTION_SQS_POLICY_NAME = "WalterBackend-${var.component}-Base-SQS-Policy-${var.domain}"
  BASE_FUNCTION_ASSUMABLE_ROLES = [
    for entity in var.assumable_entities :
    "arn:aws:iam::${var.domain}:role/WalterBackend-${var.component}-${entity}-Role-${var.domain}"
  ]

}

module "base_function_role" {
  source      = "../iam_lambda_execution_role"
  name        = local.BASE_FUNCTION_ROLE_NAME
  description = var.description
  policies = merge({
    sts_assume_role_policy = aws_iam_policy.sts_assume_role_policy.arn,
    kms_access_policy      = aws_iam_policy.kms_access_policy.arn
    }, length(var.receive_message_queue_access_arns) > 0 ? {
    sqs_access_policy = module.base_function_role_sqs_queue_access_policy[0].policy_arn
  } : {})
}

resource "aws_iam_policy" "sts_assume_role_policy" {
  name        = local.BASE_FUNCTION_STS_POLICY_NAME
  description = "The base IAM policy for the WalterBackend ${var.component} function used to assume execution roles."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "sts:AssumeRole",
        ]
        Effect   = "Allow"
        Resource = local.BASE_FUNCTION_ASSUMABLE_ROLES
      }
    ]
  })
}

resource "aws_iam_policy" "kms_access_policy" {
  name        = local.BASE_FUNCTION_KMS_POLICY_NAME
  description = "The base IAM policy for the WalterBackend ${var.component} function used to encrypt and decrypt env vars with KMS keys."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "kms:*"
        ]
        Effect   = "Allow"
        Resource = var.kms_key_arns
      }
    ]
  })
}

module "base_function_role_sqs_queue_access_policy" {
  count       = length(var.receive_message_queue_access_arns) > 0 ? 1 : 0
  source      = "../iam_sqs_queue_access_policy"
  name        = local.BASE_FUNCTION_SQS_POLICY_NAME
  queue_arns  = var.receive_message_queue_access_arns
  access_type = "consumer"
}
