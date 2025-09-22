locals {
  # Capture "us-east-1" and "a"
  az_parts = regex("^(.*[0-9])([a-z])$", var.availability_zone)

  region_abbreviations = {
    "us-east-1"      = "USE1"
    "us-east-2"      = "USE2"
    "us-west-1"      = "USW1"
    "us-west-2"      = "USW2"
    "ca-central-1"   = "CAC1"
    "eu-central-1"   = "EUC1"
    "eu-west-1"      = "EUW1"
    "eu-west-2"      = "EUW2"
    "eu-west-3"      = "EUW3"
    "ap-south-1"     = "APS1"
    "ap-northeast-1" = "APNE1"
    "ap-northeast-2" = "APNE2"
    "ap-northeast-3" = "APNE3"
    "ap-southeast-1" = "APSE1"
    "ap-southeast-2" = "APSE2"
    "sa-east-1"      = "SAE1"
  }

  az_short = format(
    "%s%s",
    lookup(local.region_abbreviations, local.az_parts[0], upper(local.az_parts[0])),
    upper(local.az_parts[1])
  )
}


resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = "${var.name}-VPC-${var.domain}" }
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id
  tags   = { Name = "${var.name}-IGW-${var.domain}" }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = true
  tags                    = { Name = "${var.name}-PublicSubnet-${local.az_short}-${var.domain}" }
}

resource "aws_subnet" "private" {
  vpc_id            = aws_vpc.this.id
  cidr_block        = var.private_subnet_cidr
  availability_zone = var.availability_zone
  tags              = { Name = "${var.name}-PrivateSubnet-${local.az_short}-${var.domain}" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id
  tags   = { Name = "${var.name}-PublicRouteTable-${var.domain}" }
}

resource "aws_route" "public_internet_access" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.this.id
}

resource "aws_route_table_association" "public_assoc" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_eip" "nat" {
  domain = "vpc"
  tags   = { Name = "${var.name}-NATGW-EIP-${var.domain}" }

  depends_on = [
    aws_internet_gateway.this
  ]
}

resource "aws_nat_gateway" "this" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public.id
  tags          = { Name = "${var.name}-NATGW-${var.domain}" }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.this.id
  tags   = { Name = "${var.name}-PrivateRouteTable-${var.domain}" }
}

resource "aws_route" "private_nat_gateway" {
  route_table_id         = aws_route_table.private.id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.this.id
}

resource "aws_route_table_association" "private_assoc" {
  subnet_id      = aws_subnet.private.id
  route_table_id = aws_route_table.private.id
}

resource "aws_security_group" "function_sg" {
  name        = "${var.name}-Function-SG-${var.domain}"
  description = "The security group for WalterBackend functions. (${var.domain}) "
  vpc_id      = aws_vpc.this.id

  # Lambda needs outbound access to NAT Gateway / Internet
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.name}-Function-SG-${var.domain}"
  }
}

resource "aws_vpc_endpoint" "dynamodb" {
  vpc_id            = aws_vpc.this.id
  service_name      = "com.amazonaws.${var.region}.dynamodb"
  vpc_endpoint_type = "Gateway"

  # Associate with the private route table so private subnets can reach DynamoDB
  route_table_ids = [aws_route_table.private.id]

  tags = {
    Name = "${var.name}-VPCE-DynamoDB-${var.domain}"
  }
}

resource "aws_vpc_endpoint" "secretsmanager" {
  vpc_id              = aws_vpc.this.id
  service_name        = "com.amazonaws.${var.region}.secretsmanager"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.private.id]
  security_group_ids  = [aws_security_group.secretsmanager_vpce_sg.id]
  private_dns_enabled = true

  depends_on = [aws_security_group.secretsmanager_vpce_sg]

  tags = {
    Name = "${var.name}-VPCE-SecretsManager-${var.domain}"
  }
}

resource "aws_security_group" "secretsmanager_vpce_sg" {
  name        = "${var.name}-SecretsManagerVPCE-SG-${var.domain}"
  description = "SG for Secrets Manager VPC endpoint. (${var.domain})"
  vpc_id      = aws_vpc.this.id

  # Allow Lambda SG to reach endpoint on 443
  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.function_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.name}-SecretsManagerVPCE-SG-${var.domain}"
  }
}


