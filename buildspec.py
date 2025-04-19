"""
BuildSpec

This script is responsible for deploying infrastructure updates to
WalterAIBackend. The infrastructure for the service is maintained by
a CloudFormation stack and this script ensures the stack is always up
to date. If the stack does not exist, this script creates it and if
the stack does exist and the stack contains changes, it executes the
change set. This script is executed by CodeBuild during builds prior
to CodeDeploy bumping the Lambda versions.
"""

import os
import time
from typing import List

import boto3
from mypy_boto3_cloudformation import CloudFormationClient
from mypy_boto3_events.client import EventBridgeClient
from mypy_boto3_s3 import S3Client
from src.config import CONFIG

from src.environment import get_domain

#############
# ARGUMENTS #
#############

DOMAIN = get_domain(os.getenv("DOMAIN", "DEVELOPMENT"))
"""(str): The domain of Walter."""

REGION = os.getenv("AWS_REGION", "us-east-1")
"""(str): The region of Walter."""

STACK_NAME = f"WalterBackend-{DOMAIN.value}"
"""(str): The name of the CloudFormation stack for all WalterBackend infrastructure."""

BUCKET = "walter-backend-src"
"""(str): The name of the S3 bucket that contains all the source code for WalterBackend"""

ADD_NEWS_SUMMARY_REQUESTS_WORFKLOW_TRIGGER_NAME = (
    f"WalterWorkflow-AddNewsSummaryRequestsTrigger-{DOMAIN.value}"
)
"""(str): The EventBridge cron schedule used to trigger the AddNewsSummaryRequests workflow."""

ADD_NEWSLETTER_REQUESTS_WORKFLOW_TRIGGER_NAME = (
    f"WalterWorkflow-AddNewsletterRequestsTrigger-{DOMAIN.value}"
)
"""(str): The EventBridge cron schedule used to trigger the AddNewsletterRequests workflow."""

TEMPLATE_URL = "https://walter-backend-src.s3.us-east-1.amazonaws.com/infra.yml"
"""(str): The template url of the CloudFormation YAML file to use for infrastructure updates."""

CHANGE_SET_NAME = f"WalterBackendChangeSet-{DOMAIN.value}"
"""(str): The name of the change set to update CloudFormation WalterBacked infrastructure."""

###########
# METHODS #
###########


def update_add_news_summary_requests_workflow_trigger(client: EventBridgeClient) -> str:
    client.put_rule(
        Name=ADD_NEWS_SUMMARY_REQUESTS_WORFKLOW_TRIGGER_NAME,
        ScheduleExpression=CONFIG.news_summary.schedule,
        State="ENABLED",
    )


def update_add_newsletter_requests_workflow_trigger(client: EventBridgeClient) -> str:
    client.put_rule(
        Name=ADD_NEWSLETTER_REQUESTS_WORKFLOW_TRIGGER_NAME,
        ScheduleExpression=CONFIG.newsletter.schedule,
        State="ENABLED",
    )


def get_stacks(client: CloudFormationClient) -> List[str]:
    stacks = client.list_stacks()

    # get not deleted stacks
    return [
        summary["StackName"]
        for summary in stacks["StackSummaries"]
        if "DELETE" not in summary["StackStatus"]
    ]


def stack_exists(client: CloudFormationClient) -> bool:
    return STACK_NAME in get_stacks(client)


def create_stack(client: CloudFormationClient) -> None:
    client.create_stack(
        StackName=STACK_NAME,
        TemplateURL=TEMPLATE_URL,
        Parameters=[{"ParameterKey": "AppEnvironment", "ParameterValue": DOMAIN.value}],
        Capabilities=["CAPABILITY_NAMED_IAM"],
    )
    time.sleep(120)


def create_change_set(client: CloudFormationClient) -> None:
    client.create_change_set(
        StackName=STACK_NAME,
        TemplateURL=TEMPLATE_URL,
        Parameters=[{"ParameterKey": "AppEnvironment", "ParameterValue": DOMAIN.value}],
        Capabilities=["CAPABILITY_NAMED_IAM"],
        ChangeSetType="UPDATE",
        ChangeSetName=CHANGE_SET_NAME,
        Description=f"This change set tests updates for {STACK_NAME}.",
    )
    time.sleep(20)


def describe_change_set(client: CloudFormationClient) -> str:
    return client.describe_change_set(
        StackName=STACK_NAME,
        ChangeSetName=CHANGE_SET_NAME,
    )["Status"]


def change_set_contains_changes(status: str) -> bool:
    return status in ["CREATE_PENDING", "CREATE_IN_PROGRESS", "CREATE_COMPLETE"]


def execute_change_set(client: CloudFormationClient) -> None:
    time.sleep(20)
    client.execute_change_set(StackName=STACK_NAME, ChangeSetName=CHANGE_SET_NAME)


def delete_change_set(client: CloudFormationClient) -> None:
    client.delete_change_set(StackName=STACK_NAME, ChangeSetName=CHANGE_SET_NAME)


def upload_template(client: S3Client) -> None:
    client.upload_file(Bucket=BUCKET, Key="infra.yml", Filename="./infra/infra.yml")


##########
# SCRIPT #
##########

events = boto3.client("events", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)
cloudformation = boto3.client("cloudformation", region_name=REGION)

print("Updating WalterWorkflow triggers...")
update_add_news_summary_requests_workflow_trigger(events)
update_add_newsletter_requests_workflow_trigger(events)

print("Uploading CloudFormation template to S3...")
upload_template(s3)

print(f"Checking if stack '{STACK_NAME}' exists...")
if stack_exists(cloudformation):
    print(f"Stack '{STACK_NAME}' exists! Creating change set...")
    create_change_set(cloudformation)
    status = describe_change_set(cloudformation)
    print(f"Change set status: {status}")

    if change_set_contains_changes(status):
        print("Change set contains changes! Executing change set...")
        execute_change_set(cloudformation)

    print("Deleting change set...")
    delete_change_set(cloudformation)
else:
    print(f"Stack '{STACK_NAME}' does not exist! Creating stack...")
    create_stack(cloudformation)
