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

APP_ENVIRONMENT = AppEnvironment.DEVELOPMENT.value
"""(str): The application environment of WalterBackend to deploy."""

AWS_ACCOUNT_ID = "010526272437"
"""(str): The AWS account ID of the WalterAI."""

AWS_REGION = "us-east-1"
"""(str): The AWS deployment region."""

VERSION = "0.0.0"
"""(str): The version of WalterBackend image to build, upload, and tag."""

VERSION_TAG = f"v{VERSION}"
"""(str): The version tag of WalterBackend image to build, upload, and tag."""

RELEASE_DESCRIPTION = "The initial release of WalterBackend."
"""(str): The release description for the git tag."""

WALTER_BACKEND_IMAGE_URI = f"{AWS_ACCOUNT_ID}.dkr.ecr.{AWS_REGION}.amazonaws.com/walter-backend-{APP_ENVIRONMENT}:{VERSION}"
"""(str): The URI of the WalterBackend image to deploy."""

LAMBDA_FUNCTIONS: List[str] = [
    f"WalterBackend-API-{APP_ENVIRONMENT}",
    f"WalterBackend-Canary-{APP_ENVIRONMENT}",
    f"WalterBackend-Workflow-{APP_ENVIRONMENT}",
]
"""(List[str]): The names of the Lambda functions to deploy."""

FUNCTION_ALIAS: str = "release"
"""(str): The alias for the current Lambda function version used by WalterBackend."""


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

    print("Initializing S3 client...")
    s3_client = boto3.client("s3", region_name=AWS_REGION)

    print("Initializing ECR client...")
    ecr_client = boto3.client("ecr", region_name=AWS_REGION)

    print("Initializing Lambda client...")
    lambda_client = boto3.client("lambda", region_name=AWS_REGION)

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
    print_build_step_header(
        f"BUILD AND UPLOAD WALTER BACKEND IMAGE '{VERSION_TAG}'", APP_ENVIRONMENT
    )

    print("Getting authorization token from ECR...")

    # get an authorization token from ecr and extract username, password, and endpoint for docker login
    auth_data = ecr_client.get_authorization_token()["authorizationData"][0]
    token = auth_data["authorizationToken"]
    endpoint = auth_data["proxyEndpoint"]
    username, password = base64.b64decode(token).decode("utf-8").split(":")

    print("Building and uploading image...")

    # build and tag the versioned image
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
    # the following command builds the latest image with the
    # corresponding tag
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

    # tag the latest image with the versioned tag
    run_cmd(
        [
            "docker",
            "tag",
            "walter-backend:latest",
            WALTER_BACKEND_IMAGE_URI,
        ]
    )

    # push the versioned image to ecr
    run_cmd(
        [
            "docker",
            "push",
            WALTER_BACKEND_IMAGE_URI,
        ]
    )

    print(f"WalterBackend image '{VERSION_TAG}' built and uploaded successfully!")


# def create_git_tag(version: str, description: str) -> None:
#     """
#     Create a git tag for the given version.
#
#     Args:
#         version: The semantic version of the git tag.
#         description: The description of the git tag.
#     """
#     print_build_step_header(
#         f"CREATE WALTER BACKEND GIT TAG '{version}'", APP_ENVIRONMENT
#     )
#
#     print(
#         f"Creating git tag with the following details:\nVersion: {version}\nDescription: {description}"
#     )
#
#     if tag_exists(version):
#         print(f"Warning: Tag {version} already exists locally, deleting...")
#         run_cmd(["git", "tag", "-d", version])
#
#         # check if tag exists remotely before deleting
#         try:
#             output = run_cmd(["git", "ls-remote", "--tags", "origin", version])
#             if output and f"refs/tags/{version}" in output:
#                 print(f"Remote tag {version} exists, deleting...")
#                 run_cmd(["git", "push", "origin", f":refs/tags/{version}"])
#             else:
#                 print(f"Remote tag {version} does not exist, skipping remote deletion")
#         except Exception as e:
#             print(f"Warning: Could not check/delete remote tag {version}: {e}")
#
#     try:
#         run_cmd(["git", "tag", "-a", version, "-m", description])
#         run_cmd(["git", "push", "origin", version])
#         print(f"Created and pushed git tag: {version}")
#     except Exception as e:
#         print(f"Warning: Could not create/push git tag {version}: {e}")


# def tag_exists(version: str) -> bool:
#     """
#     Check if a git tag exists at the given version.
#
#     Args:
#         version: The semantic version of the git tag
#             to check.
#
#     Returns:
#         (bool): True if the tag exists, False otherwise.
#     """
#     print(f"Checking for existing tag '{version}'...")
#
#     try:
#         run_cmd(["git", "rev-parse", version])
#         print(f"Found existing git tag '{version}'!")
#         return True
#     except subprocess.CalledProcessError:
#         print(f"No git tag '{version}' found...")
#         return False


def update_functions(lambda_client: LambdaClient, functions: List[str]) -> None:
    print_build_step_header(
        f"UPDATE WALTER BACKEND FUNCTIONS '{VERSION_TAG}'", APP_ENVIRONMENT
    )

    print(
        f"Updating function code to WalterBackend version '{VERSION_TAG}':\n{json.dumps(functions, indent=4)}"
    )
    for func in functions:
        lambda_client.update_function_code(
            FunctionName=func,
            ImageUri=WALTER_BACKEND_IMAGE_URI,
        )
    sleep(30)


def publish_functions(lambda_client: LambdaClient, functions: List[str]) -> None:
    print_build_step_header(
        f"PUBLISH WALTER BACKEND FUNCTIONS '{VERSION_TAG}'", APP_ENVIRONMENT
    )

    print(f"Publishing new function versions:\n{json.dumps(functions, indent=4)}")
    for func in functions:
        lambda_client.publish_version(
            FunctionName=func,
        )

    print("Waiting for new function versions to become active...")
    sleep(30)


def update_aliases(lambda_client: LambdaClient, functions: List[str]) -> None:
    print_build_step_header(
        f"UPDATE WALTER BACKEND FUNCTION ALIASES '{VERSION_TAG}'", APP_ENVIRONMENT
    )

    print("Getting latest function versions...")

    latest_versions = {}
    for func in functions:
        response = lambda_client.list_versions_by_function(FunctionName=func)
        versions = []
        for v in response["Versions"]:
            version = v["Version"]
            if version == "$LATEST":
                continue
            versions.append(int(version))
        versions.sort()
        latest_version = versions[-1]
        latest_versions[func] = latest_version

    print(f"Latest function versions:\n{json.dumps(latest_versions, indent=4)}")

    print("Updating function aliases...")

    for func, version in latest_versions.items():
        lambda_client.update_alias(
            FunctionName=func,
            Name=FUNCTION_ALIAS,
            FunctionVersion=str(version),
        )
        print(
            f"Updated alias '{FUNCTION_ALIAS}' for function '{func}' to version {version}"
        )


##########
# SCRIPT #
##########


s3_client, ecr_client, lambda_client = create_boto3_clients()

update_docs(s3_client)
build_and_upload_image(ecr_client)
update_functions(lambda_client, LAMBDA_FUNCTIONS)
publish_functions(lambda_client, LAMBDA_FUNCTIONS)
update_aliases(lambda_client, LAMBDA_FUNCTIONS)
