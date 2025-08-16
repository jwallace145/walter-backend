import base64
import json
import subprocess
import sys
from enum import Enum
from time import sleep
from typing import Dict, List

import boto3
from jinja2 import Template
from mypy_boto3_cloudformation import CloudFormationClient
from mypy_boto3_ecr import ECRClient
from mypy_boto3_lambda import LambdaClient
from mypy_boto3_s3 import S3Client

##########
# MODELS #
##########


class AppEnvironment(Enum):
    """The application environment."""

    DEVELOPMENT = "dev"


#############
# CONSTANTS #
#############

AWS_REGION = "us-east-1"
"""(str): The AWS deployment region."""

APP_ENVIRONMENT = AppEnvironment.DEVELOPMENT.value
"""(str): The application environment of the WalterAPI to deploy."""

WALTER_API_IMAGE_URI = "010526272437.dkr.ecr.us-east-1.amazonaws.com/walter/api:latest"
"""(str): The URI of the Walter API image to deploy."""

WALTER_API_SOURCE_CODE = "s3://walter-backend-src/walter-backend.zip"
"""(str): The source code of the Walter API to deploy."""

WALTER_API_CFN_STACK_NAME = "WalterBackend-dev"
"""(str): The name of the CloudFormation stack to deploy the Walter API to."""

WALTER_API_CFN_TEMPLATE_URL = (
    "https://walter-backend-src.s3.us-east-1.amazonaws.com/infra.yml"
)
"""(str): The template url of the CloudFormation YAML file to use for infrastructure updates."""

LAMBDA_FUNCTIONS = [
    f"WalterAPI-{APP_ENVIRONMENT}",
    f"WalterCanary-{APP_ENVIRONMENT}",
    f"WalterWorkflows-{APP_ENVIRONMENT}",
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


def update_docs(s3_client: S3Client) -> None:
    """
    This function uploads the OpenAPI specification file to the WalterAPI documentation S3 bucket.

    This ensures that the API documentation is always up-to-date with the latest API specifications.

    Args:
        s3_client: The boto3 S3 client.

    Returns:
        None
    """
    print("Updating WalterAPI documentation...")
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
    print("Building and uploading WalterAPI image...")

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
            "walter/api",
            "--load",
            ".",
        ]
    )
    run_cmd(
        [
            "docker",
            "tag",
            "walter/api:latest",
            WALTER_API_IMAGE_URI,
        ]
    )

    # push the latest image to ecr
    run_cmd(
        [
            "docker",
            "push",
            WALTER_API_IMAGE_URI,
        ]
    )

    print("WalterAPI image built and uploaded successfully!")


def update_source_code(lambda_client: LambdaClient, functions) -> None:
    print("Updating WalterAPI function code...")
    for func in functions:
        lambda_client.update_function_code(
            FunctionName=func,
            ImageUri=WALTER_API_IMAGE_URI,
        )
    sleep(30)


def increment_versions(lambda_client: LambdaClient, functions) -> None:
    print("Increment Lambda function versions...")
    for func in functions:
        print(f"Incrementing version of {func}...")
        lambda_client.publish_version(FunctionName=func)
    sleep(30)


def get_latest_versions(lambda_client: LambdaClient, functions) -> Dict[str, str]:
    print("Getting latest version of Lambda functions...")
    paginator = lambda_client.get_paginator("list_versions_by_function")

    latest_versions = {}
    for func in functions:
        versions = []
        for page in paginator.paginate(FunctionName=func):
            versions.extend(page["Versions"])

        latest_version = sorted(
            versions,
            key=lambda v: int(v["Version"]) if v["Version"] != "$LATEST" else -1,
        )[-1]["Version"]

        if func == f"WalterAPI-{APP_ENVIRONMENT}":
            latest_versions["walter_api_version"] = latest_version
        if func == f"WalterCanary-{APP_ENVIRONMENT}":
            latest_versions["walter_canary_version"] = latest_version
        if func == f"WalterWorkflows-{APP_ENVIRONMENT}":
            latest_versions["walter_workflows_version"] = latest_version

    return latest_versions


def create_cfn_template_with_latest_api_versions(
    latest_api_versions: Dict[str, str],
    cfn_template_path: str = "./infra/infra.yml.j2",
    cfn_output_file: str = "./infra/infra.yml",
) -> None:
    print("Creating CFN template with latest API versions...")
    with open(cfn_template_path) as f:
        template = Template(f.read())

    rendered = template.render(**latest_api_versions)
    with open(cfn_output_file, "w") as f:
        f.write(rendered)


def get_stacks(client: CloudFormationClient) -> List[str]:
    stacks = client.list_stacks()

    # get not deleted stacks
    return [
        summary["StackName"]
        for summary in stacks["StackSummaries"]
        if "DELETE" not in summary["StackStatus"]
    ]


def stack_exists(client: CloudFormationClient) -> bool:
    print(f"Checking if stack '{WALTER_API_CFN_STACK_NAME}' exists...")
    return WALTER_API_CFN_STACK_NAME in get_stacks(client)


def create_stack(client: CloudFormationClient) -> None:
    client.create_stack(
        StackName=WALTER_API_CFN_STACK_NAME,
        TemplateURL=WALTER_API_CFN_TEMPLATE_URL,
        Parameters=[{"ParameterKey": "AppEnvironment", "ParameterValue": "dev"}],
        Capabilities=["CAPABILITY_NAMED_IAM"],
    )
    sleep(120)


def create_change_set(client: CloudFormationClient) -> None:
    print(f"Stack '{WALTER_API_CFN_STACK_NAME}' exists! Creating change set...")
    client.create_change_set(
        StackName=WALTER_API_CFN_STACK_NAME,
        TemplateURL=WALTER_API_CFN_TEMPLATE_URL,
        Parameters=[{"ParameterKey": "AppEnvironment", "ParameterValue": "dev"}],
        Capabilities=["CAPABILITY_NAMED_IAM"],
        ChangeSetType="UPDATE",
        ChangeSetName="WalterBackend-dev-ChangeSet",
        Description=f"This change set tests updates for {WALTER_API_CFN_STACK_NAME}.",
    )
    sleep(30)


def describe_change_set(client: CloudFormationClient) -> str:
    return client.describe_change_set(
        StackName=WALTER_API_CFN_STACK_NAME,
        ChangeSetName="WalterBackend-dev-ChangeSet",
    )["Status"]


def change_set_contains_changes(status: str) -> bool:
    return status in ["CREATE_PENDING", "CREATE_IN_PROGRESS", "CREATE_COMPLETE"]


def execute_change_set(client: CloudFormationClient) -> None:
    sleep(60)
    client.execute_change_set(
        StackName=WALTER_API_CFN_STACK_NAME, ChangeSetName="WalterBackend-dev-ChangeSet"
    )


def delete_change_set(client: CloudFormationClient) -> None:
    client.delete_change_set(
        StackName=WALTER_API_CFN_STACK_NAME, ChangeSetName="WalterBackend-dev-ChangeSet"
    )


def upload_cfn_template(client: S3Client) -> None:
    print("Uploading CloudFormation template to S3...")
    client.upload_file(
        Bucket="walter-backend-src", Key="infra.yml", Filename="./infra/infra.yml"
    )


###########
# CLIENTS #
###########

print("Creating Boto3 clients...")
cloudformation_client = boto3.client("cloudformation", region_name=AWS_REGION)
ecr_client = boto3.client("ecr", region_name=AWS_REGION)
lambda_client = boto3.client("lambda", region_name=AWS_REGION)
s3_client = boto3.client("s3", region_name=AWS_REGION)

##########
# SCRIPT #
##########

update_docs(s3_client)
build_and_upload_image(ecr_client)
update_source_code(lambda_client, LAMBDA_FUNCTIONS)
increment_versions(lambda_client, LAMBDA_FUNCTIONS)
latest_versions = get_latest_versions(lambda_client, LAMBDA_FUNCTIONS)
print(f"The latest API versions:\n{json.dumps(latest_versions, indent=4)}")
create_cfn_template_with_latest_api_versions(latest_versions)
upload_cfn_template(s3_client)

if stack_exists(cloudformation_client):
    create_change_set(cloudformation_client)
    status = describe_change_set(cloudformation_client)
    print(f"Change set status: {status}")

    if change_set_contains_changes(status):
        print("Change set contains changes! Executing change set...")
        execute_change_set(cloudformation_client)

    print("Deleting change set...")
    delete_change_set(cloudformation_client)
else:
    print(f"Stack '{WALTER_API_CFN_STACK_NAME}' does not exist! Creating stack...")
    create_stack(cloudformation_client)
