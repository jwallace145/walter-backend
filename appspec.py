"""
AppSpec Generator

This script is responsible for creating an `appspec.yml` file for
CodeDeploy deployments to bump the WalterAIBackend lambda from its
current version to the latest version. This script is run during
builds executed by CodeBuild and the output generated by this script
is dumped to S3 as an artifact to be used by CodeDeploy to execute
the deployment.
"""

import os

import boto3
from src.environment import get_domain
from mypy_boto3_lambda import LambdaClient

############
# TEMPLATE #
############

APPSPEC_FILE_NAME = "appspec.yml"

APPSPEC_TEMPLATE = """
version: 0.0

Resources:
  - MyFunction:
      Type: AWS::Lambda::Function
      Properties:
        Name: "WalterBackend-{domain}"
        Alias: "WalterBackend-{domain}"
        CurrentVersion: "{current_walter_backend__version}"
        TargetVersion: "{target_walter_backend_version}"

  - MyFunction:
      Type: AWS::Lambda::Function
      Properties:
        Name: "WalterAPI-{domain}"
        Alias: "WalterAPI-{domain}"
        CurrentVersion: "{current_walter_api_version}"
        TargetVersion: "{target_walter_api_version}"
"""

#############
# ARGUMENTS #
#############

DOMAIN = get_domain(os.getenv("DOMAIN", "DEVELOPMENT"))

REGION = os.getenv("AWS_REGION", "us-east-1")

WALTER_BACKEND_LAMBDA_NAME = f"WalterBackend-{DOMAIN.value}"

WALTER_BACKEND_LAMBDA_ALIAS = f"WalterBackend-{DOMAIN.value}"

WALTER_API_LAMBDA_NAME = f"WalterAPI-{DOMAIN.value}"

WALTER_API_LAMBDA_ALIAS = f"WalterAPI-{DOMAIN.value}"

###########
# METHODS #
###########


def get_current_version(
    lambda_client: LambdaClient, lambda_name: str, lambda_alias: str
) -> str:
    return lambda_client.get_alias(FunctionName=lambda_name, Name=lambda_alias)[
        "FunctionVersion"
    ]


def get_target_version(lambda_client: LambdaClient, lambda_name: str) -> str:
    return lambda_client.list_versions_by_function(FunctionName=lambda_name)[
        "Versions"
    ][-1]["Version"]


def create_appspec(
    current_walter_backend_version: str,
    target_walter_backend_version: str,
    current_walter_api_version: str,
    target_walter_api_version: str,
) -> None:
    with open(APPSPEC_FILE_NAME, "w") as appspec:
        appspec.write(
            APPSPEC_TEMPLATE.format(
                current_walter_backend_version=current_walter_backend_version,
                target_walter_backend_version=target_walter_backend_version,
                current_walter_api_version=current_walter_api_version,
                target_walter_api_version=target_walter_api_version,
                domain=DOMAIN.value,
            )
        )


##########
# SCRIPT #
##########

lambda_client: LambdaClient = boto3.client("lambda", region_name=REGION)

current_walter_backend_version = get_current_version(
    lambda_client, WALTER_BACKEND_LAMBDA_NAME, WALTER_BACKEND_LAMBDA_ALIAS
)
target_walter_backend_version = get_target_version(
    lambda_client, WALTER_BACKEND_LAMBDA_NAME
)

current_walter_api_version = get_current_version(
    lambda_client, WALTER_API_LAMBDA_NAME, WALTER_API_LAMBDA_ALIAS
)
target_walter_api_version = get_target_version(lambda_client, WALTER_API_LAMBDA_NAME)

create_appspec(
    current_walter_backend_version,
    target_walter_backend_version,
    current_walter_api_version,
    target_walter_api_version,
)
