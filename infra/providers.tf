terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "walter-backend-dev-terraform-state-12dd1836"
    key            = "terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "walter-backend-dev-terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      service : "WalterBackend"
      domain : var.domain
    }
  }
}