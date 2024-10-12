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
from src.environment import get_domain

#############
# ARGUMENTS #
#############

DOMAIN = get_domain(os.getenv("DOMAIN", "DEVELOPMENT"))

REGION = os.getenv("AWS_REGION", "us-east-1")

STACK_NAME = f"WalterAIBackend-{DOMAIN.value}"

CLOUDFORMATION_TEMPLATE = "./infra/infra.yml"

CHANGE_SET_NAME = f"WalterAIBackendChangeSet-{DOMAIN.value}"

###########
# METHODS #
###########


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
        TemplateBody=open(CLOUDFORMATION_TEMPLATE).read(),
        Parameters=[{"ParameterKey": "AppEnvironment", "ParameterValue": DOMAIN.value}],
        Capabilities=["CAPABILITY_NAMED_IAM"],
    )
    time.sleep(120)


def create_change_set(client: CloudFormationClient) -> None:
    client.create_change_set(
        StackName=STACK_NAME,
        TemplateBody=open(CLOUDFORMATION_TEMPLATE).read(),
        Parameters=[{"ParameterKey": "AppEnvironment", "ParameterValue": DOMAIN.value}],
        Capabilities=["CAPABILITY_NAMED_IAM"],
        ChangeSetType="UPDATE",
        ChangeSetName=CHANGE_SET_NAME,
        Description=f"This change set tests updates for {STACK_NAME}.",
    )
    time.sleep(30)


def describe_change_set(client: CloudFormationClient) -> str:
    return client.describe_change_set(
        StackName=STACK_NAME,
        ChangeSetName=CHANGE_SET_NAME,
    )["Status"]


def change_set_contains_changes(status: str) -> bool:
    return status in ["CREATE_PENDING", "CREATE_IN_PROGRESS", "CREATE_COMPLETE"]


def execute_change_set(client: CloudFormationClient) -> None:
    time.sleep(30)
    client.execute_change_set(StackName=STACK_NAME, ChangeSetName=CHANGE_SET_NAME)


def delete_change_set(client: CloudFormationClient) -> None:
    client.delete_change_set(StackName=STACK_NAME, ChangeSetName=CHANGE_SET_NAME)


##########
# SCRIPT #
##########


cloudformation = boto3.client("cloudformation", region_name=REGION)

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
