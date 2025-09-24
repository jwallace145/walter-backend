import base64
import json
import subprocess
import sys
from enum import Enum
from time import sleep
from typing import Dict, List

import boto3
from mypy_boto3_ecr import ECRClient
from mypy_boto3_lambda import LambdaClient
from mypy_boto3_s3 import S3Client
from mypy_boto3_sts.client import STSClient

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


def log_build_vars() -> None:
    print_build_step_header("BUILD VARS", APP_ENVIRONMENT)

    print("Building new WalterBackend version with the following build variables:\n")

    build_info = {
        "WalterBackend version": VERSION,
        "WalterBackend image URI": WALTER_BACKEND_IMAGE_URI,
        "Lambda functions": json.dumps(LAMBDA_FUNCTIONS, indent=4),
        "Function alias": FUNCTION_ALIAS,
        "Release description": RELEASE_DESCRIPTION,
        "AWS region": AWS_REGION,
        "AWS account ID": AWS_ACCOUNT_ID,
        "Application environment": APP_ENVIRONMENT,
    }

    for key, value in build_info.items():
        print(f"{key}: {value}")


def log_build_identity(sts_client: STSClient) -> None:
    print_build_step_header("BUILD IDENTITY", APP_ENVIRONMENT)

    print("Getting caller identity...")
    caller_identity = sts_client.get_caller_identity()
    print(f"Account ID: {caller_identity['Account']}")
    print(f"User ID: {caller_identity['UserId']}")
    print(f"ARN: {caller_identity['Arn']}")


def create_boto3_clients() -> tuple[S3Client, ECRClient, LambdaClient, STSClient]:
    print_build_step_header("INITIALIZING BOTO3 CLIENTS", APP_ENVIRONMENT)

    print("Initializing S3 client...")
    s3_client = boto3.client("s3", region_name=AWS_REGION)

    print("Initializing ECR client...")
    ecr_client = boto3.client("ecr", region_name=AWS_REGION)

    print("Initializing Lambda client...")
    lambda_client = boto3.client("lambda", region_name=AWS_REGION)

    print("Initializing STS client...")
    sts_client = boto3.client("sts", region_name=AWS_REGION)

    return s3_client, ecr_client, lambda_client, sts_client


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


def get_latest_function_versions(
    lambda_client: LambdaClient, functions: List[str]
) -> Dict[str, int]:
    print_build_step_header(
        f"LATEST FUNCTION VERSIONS '{VERSION_TAG}'", APP_ENVIRONMENT
    )

    print(f"Getting latest function versions:\n{json.dumps(functions, indent=4)}")
    func_versions = {}

    paginator = lambda_client.get_paginator("list_versions_by_function")

    for func in functions:
        versions: list[str] = []

        for page in paginator.paginate(FunctionName=func):
            versions.extend(
                v["Version"] for v in page["Versions"] if v["Version"] != "$LATEST"
            )

        latest_version = max(map(int, versions)) if versions else None
        func_versions[func] = latest_version

    print(f"Latest function versions:\n{json.dumps(func_versions, indent=4)}")

    return func_versions


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


def update_aliases(lambda_client: LambdaClient, functions: Dict[str, int]) -> None:
    print_build_step_header(
        f"UPDATE WALTER BACKEND FUNCTION ALIASES '{VERSION_TAG}'", APP_ENVIRONMENT
    )

    print(
        f"Updating function aliases to the latest function versions:\n{json.dumps(functions, indent=4)}"
    )

    release_versions = {}
    for func, version in functions.items():
        lambda_client.update_alias(
            FunctionName=func,
            Name=FUNCTION_ALIAS,
            FunctionVersion=str(version),
        )
        release_versions[f"{func}:{FUNCTION_ALIAS}"] = version

    print(
        f"Updated function aliases to the following versions:\n{json.dumps(release_versions, indent=4)}"
    )


###########
# GIT TAG #
###########


def ensure_git_tag() -> None:
    """
    Ensures the current commit is tagged with VERSION_TAG and pushed to origin.

    Behavior:
    - Fetches tags to ensure local state is up-to-date.
    - If the tag already exists (locally or remotely), it is deleted locally and remotely.
    - Creates (or recreates) an annotated tag with RELEASE_DESCRIPTION.
    - Pushes the tag to origin (force-updated if necessary).
    """
    print_build_step_header(f"APPLY GIT TAG '{VERSION_TAG}'", APP_ENVIRONMENT)

    # Ensure we're in a git repo
    try:
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        print("Not a git repository. Skipping git tagging step.")
        return

    # Fetch latest tags
    run_cmd(["git", "fetch", "--tags", "origin", "--force"])

    # Delete local tag if it exists
    if (
        subprocess.run(
            ["git", "rev-parse", "-q", "--verify", f"refs/tags/{VERSION_TAG}"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    ):
        print(f"Tag '{VERSION_TAG}' exists locally. Deleting local tag...")
        run_cmd(["git", "tag", "-d", VERSION_TAG])

    # Delete remote tag if it exists
    tag_exists_remote = subprocess.run(
        ["git", "ls-remote", "--tags", "origin", VERSION_TAG],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    if tag_exists_remote.returncode == 0 and tag_exists_remote.stdout.strip():
        print(f"Tag '{VERSION_TAG}' exists on remote. Deleting remote tag...")
        run_cmd(["git", "push", "--delete", "origin", VERSION_TAG])

    # Force-create the tag
    print(f"Creating annotated tag '{VERSION_TAG}'...")
    run_cmd(["git", "tag", "-fa", VERSION_TAG, "-m", RELEASE_DESCRIPTION])

    # Push the tag (force to ensure update)
    print(f"Pushing tag '{VERSION_TAG}' to origin...")
    run_cmd(["git", "push", "origin", VERSION_TAG, "--force"])


##########
# SCRIPT #
##########

log_build_vars()
s3_client, ecr_client, lambda_client, sts_client = create_boto3_clients()
log_build_identity(sts_client)
update_docs(s3_client)
build_and_upload_image(ecr_client)
ensure_git_tag()
update_functions(lambda_client, LAMBDA_FUNCTIONS)
get_latest_function_versions(lambda_client, LAMBDA_FUNCTIONS)
publish_functions(lambda_client, LAMBDA_FUNCTIONS)
latest_versions = get_latest_function_versions(lambda_client, LAMBDA_FUNCTIONS)
update_aliases(lambda_client, latest_versions)
