# TODO: Delete the WalterAPIRole references after import

resource "aws_iam_role_policy_attachment" "secrets_r_policy" {
  policy_arn = aws_iam_policy.secrets_r_policy.arn
  role       = local.walterapi_role
}

resource "aws_iam_role_policy_attachment" "db_rw_policy" {
  policy_arn = aws_iam_policy.db_rw_policy.arn
  role       = local.walterapi_role
}

resource "aws_iam_role" "api_role" {
  name = "walterbackend-api-${var.domain}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "api_role_basic_lambda_execution" {
  role       = aws_iam_role.api_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "api_role_secrets_r_policy" {
  policy_arn = aws_iam_policy.secrets_r_policy.arn
  role       = aws_iam_role.api_role.name
}

resource "aws_iam_role_policy_attachment" "api_role_db_rw_policy" {
  policy_arn = aws_iam_policy.db_rw_policy.arn
  role       = aws_iam_role.api_role.name
}

resource "aws_iam_role" "canary_role" {
  name = "walterbackend-canary-${var.domain}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "canary_role_basic_lambda_execution" {
  role       = aws_iam_role.canary_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role" "workflow_role" {
  name = "walterbackend-workflow-${var.domain}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "workflow_role_basic_lambda_execution" {
  role       = aws_iam_role.workflow_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "workflow_role_db_rw_policy" {
  role       = aws_iam_role.workflow_role.name
  policy_arn = aws_iam_policy.db_rw_policy.arn
}