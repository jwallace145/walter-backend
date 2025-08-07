import base64
import json
import os
import shutil
import subprocess
import sys
import zipfile
from time import sleep
from typing import List, Dict
from dataclasses import dataclass
from enum import Enum

import boto3
from jinja2 import Template
from mypy_boto3_cloudformation import CloudFormationClient
from mypy_boto3_s3 import S3Client


##########
# MODELS #
##########


class AppEnvironment(Enum):
    """The application environment."""

    DEVELOPMENT = "dev"


@dataclass
class WalterAPIDetails:
    """Details of a Walter API function."""

    name: str  # the name of the lambda function
    source: str  # the source artifact (S3 object or ECR image)
    key: str  # the key used to inject the latest lambda version into cfn template


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

WALTER_API_FUNCTIONS = [
    WalterAPIDetails(
        name=f"WalterAPI-AuthUser-{APP_ENVIRONMENT}",
        source=WALTER_API_IMAGE_URI,
        key="auth_user_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-AddStock-{APP_ENVIRONMENT}",
        source=WALTER_API_IMAGE_URI,
        key="add_stock_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-AddTransaction-{APP_ENVIRONMENT}",
        source=WALTER_API_IMAGE_URI,
        key="add_transaction_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-ChangePassword-{APP_ENVIRONMENT}",
        source=WALTER_API_SOURCE_CODE,
        key="change_password_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-CreateCashAccount-{APP_ENVIRONMENT}",
        source=WALTER_API_IMAGE_URI,
        key="create_cash_account_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-CreateCreditAccount-{APP_ENVIRONMENT}",
        source=WALTER_API_IMAGE_URI,
        key="create_credit_account_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-CreateLinkToken-{APP_ENVIRONMENT}",
        source=WALTER_API_IMAGE_URI,
        key="create_link_token_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-CreateUser-{APP_ENVIRONMENT}",
        source=WALTER_API_IMAGE_URI,
        key="create_user_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-DeleteCashAccount-{APP_ENVIRONMENT}",
        source=WALTER_API_IMAGE_URI,
        key="delete_cash_account_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-DeleteCreditAccount-{APP_ENVIRONMENT}",
        source=WALTER_API_IMAGE_URI,
        key="delete_credit_account_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-DeleteStock-{APP_ENVIRONMENT}",
        source=WALTER_API_IMAGE_URI,
        key="delete_stock_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-DeleteTransaction-{APP_ENVIRONMENT}",
        source=WALTER_API_IMAGE_URI,
        key="delete_transaction_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-EditTransaction-{APP_ENVIRONMENT}",
        source=WALTER_API_IMAGE_URI,
        key="edit_transaction_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-ExchangePublicToken-{APP_ENVIRONMENT}",
        source=WALTER_API_IMAGE_URI,
        key="exchange_public_token_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-GetCashAccounts-{APP_ENVIRONMENT}",
        source=WALTER_API_IMAGE_URI,
        key="get_cash_accounts_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-GetCreditAccounts-{APP_ENVIRONMENT}",
        source=WALTER_API_IMAGE_URI,
        key="get_credit_accounts_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-GetNewsletter-{APP_ENVIRONMENT}",
        source=WALTER_API_SOURCE_CODE,
        key="get_newsletter_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-GetNewsletters-{APP_ENVIRONMENT}",
        source=WALTER_API_IMAGE_URI,
        key="get_newsletters_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-GetNewsSummary-{APP_ENVIRONMENT}",
        source=WALTER_API_IMAGE_URI,
        key="get_news_summary_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-GetPortfolio-{APP_ENVIRONMENT}",
        source=WALTER_API_IMAGE_URI,
        key="get_portfolio_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-GetPrices-{APP_ENVIRONMENT}",
        source=WALTER_API_IMAGE_URI,
        key="get_prices_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-GetStatistics-{APP_ENVIRONMENT}",
        source=WALTER_API_SOURCE_CODE,
        key="get_statistics_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-GetStock-{APP_ENVIRONMENT}",
        source=WALTER_API_IMAGE_URI,
        key="get_stock_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-GetTransactions-{APP_ENVIRONMENT}",
        source=WALTER_API_IMAGE_URI,
        key="get_transactions_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-GetUser-{APP_ENVIRONMENT}",
        source=WALTER_API_IMAGE_URI,
        key="get_user_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-PurchaseNewsletterSubscription-{APP_ENVIRONMENT}",
        source=WALTER_API_SOURCE_CODE,
        key="purchase_newsletter_subscription_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-SearchStocks-{APP_ENVIRONMENT}",
        source=WALTER_API_SOURCE_CODE,
        key="search_stocks_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-SendChangePasswordEmail-{APP_ENVIRONMENT}",
        source=WALTER_API_SOURCE_CODE,
        key="send_change_password_email_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-SendNewsletter-{APP_ENVIRONMENT}",
        source=WALTER_API_SOURCE_CODE,
        key="send_newsletter_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-SendVerifyEmail-{APP_ENVIRONMENT}",
        source=WALTER_API_SOURCE_CODE,
        key="send_verify_email_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-Subscribe-{APP_ENVIRONMENT}",
        source=WALTER_API_SOURCE_CODE,
        key="subscribe_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-SyncTransactions-{APP_ENVIRONMENT}",
        source=WALTER_API_IMAGE_URI,
        key="sync_transactions_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-Unsubscribe-{APP_ENVIRONMENT}",
        source=WALTER_API_SOURCE_CODE,
        key="unsubscribe_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-UpdateCashAccount-{APP_ENVIRONMENT}",
        source=WALTER_API_IMAGE_URI,
        key="update_cash_account_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-UpdatePassword-{APP_ENVIRONMENT}",
        source=WALTER_API_IMAGE_URI,
        key="update_password_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-UpdateUser-{APP_ENVIRONMENT}",
        source=WALTER_API_IMAGE_URI,
        key="update_user_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-VerifyEmail-{APP_ENVIRONMENT}",
        source=WALTER_API_SOURCE_CODE,
        key="verify_email_api_version",
    ),
    WalterAPIDetails(
        name=f"WalterAPI-VerifyPurchaseNewsletterSubscription-{APP_ENVIRONMENT}",
        source=WALTER_API_SOURCE_CODE,
        key="verify_purchase_newsletter_subscription_api_version",
    ),
]
"""(List[WalterAPIDetails]): The list of all the Walter API functions to deploy."""

# TODO: Handle canaries deployment

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


def build_and_upload_api_image(ecr_client) -> None:
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
    run_cmd(["docker", "build", "-t", "walter/api", "."])
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


def upload_source_code(
    s3_client,
    working_dir: str = "walter-backend",
    source_dir: str = "src",
    additional_files: List[str] = ["config.yml", "walter.py"],
    artifact_name: str = "walter-backend.zip",
    s3_bucket: str = "walter-backend-src",
    s3_key: str = "walter-backend.zip",
) -> None:
    """
    Uploads source code and additional files to an Amazon S3 bucket. The function organizes
    the specified source and additional files in a working directory, zips them into an artifact,
    and uploads the zipped file to S3 using the provided S3 client. Temporary files and folders
    are automatically cleaned up after the operation.

    Args:
        s3_client: The S3 client used to interact with Amazon S3, typically an instance of boto3.client.
        working_dir: The working directory to store the intermediate copied files.
        source_dir: The source directory containing the codebase to be uploaded.
        additional_files: A list of additional file paths to include in the upload.
        artifact_name: The name of the zip artifact to be created and uploaded.
        s3_bucket: The name of the target S3 bucket.
        s3_key: The S3 key where the artifact will be stored.

    Raises:
        Exits the program with a status code of 1 if an exception occurs during the upload process.

    Returns:
        None
    """
    try:
        print("Uploading WalterAPI source code to S3...")

        # check if working directory already exists, if so, delete and recreate
        if os.path.exists(working_dir):
            shutil.rmtree(working_dir)
        os.makedirs(working_dir)

        # copy source directory into working directory along with any additional files
        print("Copying source code to working directory...")
        shutil.copytree(source_dir, os.path.join(working_dir, source_dir))
        for file in additional_files:
            shutil.copy(file, working_dir)

        print("Zipping source code...")
        with zipfile.ZipFile(artifact_name, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(working_dir):
                for file in files:
                    abs_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_path, working_dir)
                    zipf.write(abs_path, rel_path)

        print("Uploading source code to S3...")
        with open(artifact_name, "rb") as f:
            s3_client.upload_fileobj(f, s3_bucket, s3_key)
        print(f"Uploaded source code to s3://{s3_bucket}/{s3_key}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        print("Cleaning up temporary files...")
        shutil.rmtree(working_dir)
        os.remove(artifact_name)


def update_api_source_code(
    lambda_client, api_functions: List[WalterAPIDetails]
) -> None:
    print("Updating source code of all APIs...")
    for api in api_functions:
        api_name = api.name
        src = api.source

        if src.startswith("s3://"):
            print(f"Updating source code of {api_name} with S3 artifact...")
            s3_bucket, s3_key = src.replace("s3://", "").split("/", 1)
            lambda_client.update_function_code(
                FunctionName=api_name,
                S3Bucket=s3_bucket,
                S3Key=s3_key,
            )
        else:
            print(f"Updating source code of {api_name} with ECR artifact...")
            lambda_client.update_function_code(
                FunctionName=api_name,
                ImageUri=src,
            )
        sleep(1)  # sleep to slow down updating source code before incrementing version


def increment_api_version(lambda_client, api_functions: List[WalterAPIDetails]) -> None:
    print("Incrementing version of all APIs...")
    for api in api_functions:
        api_name = api.name
        print(f"Incrementing version of {api_name}...")
        lambda_client.publish_version(FunctionName=api_name)
        sleep(1)  # sleep to slow down incrementing version after updating source code


def get_latest_api_versions(
    lambda_client, api_functions: List[WalterAPIDetails]
) -> Dict[str, str]:
    print("Getting latest version of all APIs...")
    latest_versions = {}
    paginator = lambda_client.get_paginator("list_versions_by_function")

    for api in api_functions:
        api_name = api.name
        api_key = api.key
        print(f"Getting latest version of {api_name}...")

        versions = []
        for page in paginator.paginate(FunctionName=api_name):
            versions.extend(page["Versions"])

        latest_version = sorted(
            versions,
            key=lambda v: int(v["Version"]) if v["Version"] != "$LATEST" else -1,
        )[-1]["Version"]

        latest_versions[api_key] = latest_version

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

upload_source_code(s3_client)
build_and_upload_api_image(ecr_client)
update_api_source_code(lambda_client, WALTER_API_FUNCTIONS)
increment_api_version(lambda_client, WALTER_API_FUNCTIONS)
latest_api_versions = get_latest_api_versions(lambda_client, WALTER_API_FUNCTIONS)
print(f"The latest API versions:\n{json.dumps(latest_api_versions, indent=4)}")
create_cfn_template_with_latest_api_versions(latest_api_versions)
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
