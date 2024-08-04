"""
BuildSpec

This script is responsible for updating the WalterAIBackend infrastructure
when changes are detected in the CloudFormation stack for CICD purposes.
This script is executed during builds by CodeBuild and creates a test change
set to determine if the stack includes changes and if so updates the stack.
"""

import os
import time

import boto3
from src.environment import get_domain

DOMAIN = get_domain(os.getenv("DOMAIN", "DEVELOPMENT"))

REGION = os.getenv("AWS_REGION", "us-east-1")

STACK_NAME = "WalterAIBackend-Dev"

CLOUDFORMATION_TEMPLATE = "./infra/infra.yml"

CHANGE_SET_NAME = "TestChanges-WalterAIBackend-Dev"

cloudformation = boto3.client("cloudformation", region_name=REGION)

cloudformation.create_change_set(
    ChangeSetName=CHANGE_SET_NAME,
    Description="This change set tests updates for WalterAIBackend-dev",
    StackName=STACK_NAME,
    TemplateBody=open(CLOUDFORMATION_TEMPLATE).read(),
    Parameters=[{"ParameterKey": "AppEnvironment", "ParameterValue": "dev"}],
    Capabilities=["CAPABILITY_NAMED_IAM"],
    ChangeSetType="UPDATE",
)

change_set_status = cloudformation.describe_change_set(
    ChangeSetName=CHANGE_SET_NAME, StackName=STACK_NAME
)["Status"]

includes_changes = False
match change_set_status:
    case "CREATE_PENDING":
        print(
            "WalterAIBackend-dev includes changes in CREATE_PENDING state. Sleeping for 30 seconds."
        )
        includes_changes = True
        time.sleep(30)
    case "CREATE_IN_PROGRESS":
        print(
            "WalterAIBackend-dev includes changes in CREATE_IN_PROGRESS state. Sleeping for 30 seconds."
        )
        includes_changes = True
        time.sleep(30)
    case "CREATE_COMPLETED":
        print("WalterAIBackend-dev includes changes in CREATE_COMPLETE state.")
        includes_changes = True

if includes_changes:
    print("Updating WalterAIBackend-dev CloudFormation stack...")
    cloudformation.execute_change_set(
        ChangeSetName=CHANGE_SET_NAME, StackName=STACK_NAME
    )
else:
    print("WalterAIBackend-dev CloudFormation stack does not include new changes.")


print("Deleting change set...")
cloudformation.delete_change_set(ChangeSetName=CHANGE_SET_NAME, StackName=STACK_NAME)
