import base64
import json
import subprocess
import sys
from enum import Enum
from time import sleep
from typing import List

import boto3
from mypy_boto3_ecr import ECRClient
from mypy_boto3_lambda import LambdaClient
from mypy_boto3_s3 import S3Client

##########
# MODELS #
##########


class AppEnvironment(Enum):
    """The application environment."""

    DEVELOPMENT = "dev"
    STAGING = "stg"
    PRODUCTION = "prod"


#############
# CONSTANTS #
#############

AWS_REGION = "us-east-1"
"""(str): The AWS deployment region."""

APP_ENVIRONMENT = AppEnvironment.DEVELOPMENT.value
"""(str): The application environment of WalterBackend to deploy."""

WALTER_BACKEND_IMAGE_URI = (
    "010526272437.dkr.ecr.us-east-1.amazonaws.com/walter-backend:latest"
)
"""(str): The URI of the WalterBackend image to deploy."""

LAMBDA_FUNCTIONS = [
    f"WalterBackend-API-{APP_ENVIRONMENT}",
    f"WalterBackend-Canary-{APP_ENVIRONMENT}",
    f"WalterBackend-Workflow-{APP_ENVIRONMENT}",
]
"""(List[str]): The names of the Lambda functions to deploy."""


###########
# METHODS #
###########


def run_cmd(cmd: str | List[str], input_data=None) -> None:
    """
    Executes a command in the system shell or as a direct process.

    This function runs a specified command using the `subprocess.run` method and provides
    error handling. It can accept a single command string or a list of command arguments.
    On failure, the function prints an error message and exits the program with a non-zero
    exit code. It can also pass input data to the subprocess.

    Args:
        cmd (str | List[str]): The command to execute.
        input_data (Optional[Any]): An optional input to pass to the subprocess, such as
            data to send to the standard input of the command.

    Raises:
        SystemExit: Exits the program if the command execution fails.
    """
    try:
        print(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
        subprocess.run(cmd, shell=False, input=input_data, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        sys.exit(1)


def print_build_step_header(step_name: str, environment: str) -> None:
    print("\n" + "=" * 60)
    print(f"║ {step_name} ({environment})".ljust(58) + " ║")
    print("=" * 60 + "\n")


def create_boto3_clients() -> tuple[S3Client, ECRClient, LambdaClient]:
    print_build_step_header("INITIALIZING BOTO3 CLIENTS", APP_ENVIRONMENT)
    ecr_client = boto3.client("ecr", region_name=AWS_REGION)
    lambda_client = boto3.client("lambda", region_name=AWS_REGION)
    s3_client = boto3.client("s3", region_name=AWS_REGION)
    return s3_client, ecr_client, lambda_client


def update_docs(s3_client: S3Client) -> None:
    """
    This function uploads the OpenAPI specification file to the WalterAPI documentation S3 bucket.

    This ensures that the API documentation is always up-to-date with the latest API specifications.

    Args:
        s3_client: The boto3 S3 client.

    Returns:
        None
    """
    print_build_step_header("UPDATE WALTER BACKEND API DOCUMENTATION", APP_ENVIRONMENT)
    print("Uploading OpenAPI specification file to S3 bucket...")
    s3_client.upload_file(
        Bucket="walterapi-docs",
        Key="openapi.yml",
        Filename="./openapi.yml",
        ExtraArgs={"ContentType": "application/yaml"},
    )


def build_and_upload_image(ecr_client: ECRClient) -> None:
    """
    Builds and uploads the WalterAPI Docker image to an Amazon ECR repository.

    This function authenticates with the Amazon Elastic Container Registry (ECR) using an
    authorization token, builds and tags a Docker image for the WalterAPI, and then pushes
    the image to the specified ECR repository.

    Args:
        ecr_client: The boto3 ECR client.

    Returns:
        None
    """
    print_build_step_header("BUILD AND UPLOAD WALTER BACKEND IMAGE", APP_ENVIRONMENT)

    # get an authorization token from ecr and extract username, password, and endpoint for docker login
    auth_data = ecr_client.get_authorization_token()["authorizationData"][0]
    token = auth_data["authorizationToken"]
    endpoint = auth_data["proxyEndpoint"]
    username, password = base64.b64decode(token).decode("utf-8").split(":")

    # build and tag the latest image
    run_cmd(
        [
            "docker",
            "login",
            "--username",
            username,
            "--password-stdin",
            endpoint,
        ],
        input_data=password,
    )
    run_cmd(
        [
            "docker",
            "buildx",
            "build",
            "--platform=linux/arm64",
            "-t",
            "walter-backend",
            "--load",
            ".",
        ]
    )
    run_cmd(
        [
            "docker",
            "tag",
            "walter-backend:latest",
            WALTER_BACKEND_IMAGE_URI,
        ]
    )

    # push the latest image to ecr
    run_cmd(
        [
            "docker",
            "push",
            WALTER_BACKEND_IMAGE_URI,
        ]
    )

    print("WalterBackend API image built and uploaded successfully!")


def update_source_code(lambda_client: LambdaClient, functions) -> None:
    print_build_step_header("UPDATE WALTER BACKEND FUNCTIONS", APP_ENVIRONMENT)

    print(
        f"Updating WalterBackend-{APP_ENVIRONMENT} functions:\n{json.dumps(functions, indent=4)}"
    )
    for func in functions:
        lambda_client.update_function_code(
            FunctionName=func,
            ImageUri=WALTER_BACKEND_IMAGE_URI,
        )
    sleep(30)


##########
# SCRIPT #
##########

s3_client, ecr_client, lambda_client = create_boto3_clients()

# TODO: Move this logic to Terraform, update S3 bucket when OpenAPI specifications change
update_docs(s3_client)

# Not sure if Terraform can automate this yet, so we'll do it manually for now
build_and_upload_image(ecr_client)

# TODO: Move this logic to Terraform, update functions when image digest hash changes (i.e. new changes)
update_source_code(lambda_client, LAMBDA_FUNCTIONS)
