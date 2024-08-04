"""
AppSpec Generator

This script is responsible for creating an `appspec.yml` file for
CodeDeploy deployments to bump the WalterAIBackend lambda from its
current version to the latest version. This script is run during
builds executed by CodeBuild and is dumped to S3 as an artifact to
be used by CodeDeploy to execute the deployment.
"""

import os

import boto3
from src.environment import get_domain

DOMAIN = get_domain(os.getenv("DOMAIN", "DEVELOPMENT"))

REGION = os.getenv("AWS_REGION", "us-east-1")

LAMBDA_NAME = f"WalterAIBackend-{DOMAIN.value}"

LAMBDA_ALIAS = f"WalterAIBackend-{DOMAIN.value}"

APPSPEC_TEMPLATE = """
version: 0.0

Resources:
  - MyFunction:
      Type: AWS::Lambda::Function
      Properties:
        Name: "WalterAIBackend-dev"
        Alias: "WalterAIBackend-dev"
        CurrentVersion: "{current_version}"
        TargetVersion: "{target_version}"
"""

with open("./appspec.yml", "w") as appspec:
    # create lambda client
    lambda_client = boto3.client("lambda", region_name=REGION)

    # get current version the lambda is pointing to
    current_version = lambda_client.get_alias(
        FunctionName=LAMBDA_NAME, Name=LAMBDA_ALIAS
    )["FunctionVersion"]

    # get the latest version of the lambda
    target_version = lambda_client.list_versions_by_function(FunctionName=LAMBDA_NAME)[
        "Versions"
    ][-1]["Version"]

    # generate appspec file bumping lambda from current version to latest version
    appspec.write(
        APPSPEC_TEMPLATE.format(
            current_version=current_version, target_version=target_version
        )
    )
