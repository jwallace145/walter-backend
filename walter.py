import json

from src.api.common.models import HTTPStatus, Status
from src.api.routing.router import APIRouter
from src.canaries.routing.router import CanaryRouter, CanaryType
from src.utils.log import Logger
from src.workflows.common.router import WorkflowRouter

LOG = Logger(__name__).get_logger()

###############
# ENTRYPOINTS #
###############

"""
Lambda function entrypoints for different service responsibilities.

This module defines the entry functions for three distinct Lambda functions:
- API: Handles requests from API Gateway
- Workflows: Executes background tasks and database updates 
- Canaries: Runs health checks and API endpoint validation
"""


def api_entrypoint(event, context) -> dict:
    """Process API Gateway requests"""
    LOG.info("Invoking API!")
    return APIRouter.get_method(event).invoke(event).to_json()


def workflows_entrypoint(event, context) -> dict:
    """Execute asynchronous workflows for data processing and updates"""
    LOG.info("Invoking workflow!")
    return WorkflowRouter.get_workflow(event).invoke(event).to_json()


def canaries_entrypoint(event, context) -> dict:
    """Invoke API canaries to validate API health"""
    LOG.info("Invoking canaries!")

    # iterate over all canaries and invoke them
    responses = []
    for canary_type in CanaryType:
        response = CanaryRouter.get_canary(canary_type).invoke(emit_metrics=True)
        responses.append(json.loads(response["body"]))

    # count successful and failed canaries
    num_successful_canaries = 0
    num_failed_canaries = 0
    for response in responses:
        status = response["Status"]
        if status == Status.SUCCESS.value:
            num_successful_canaries += 1
        else:
            num_failed_canaries += 1

    return {
        "statusCode": HTTPStatus.OK.value,
        "body": json.dumps(
            {
                "Service": "WalterCanary",
                "Status": Status.SUCCESS.value,
                "Message": "All canaries executed successfully!",
                "Data": {
                    "num_canaries": len(responses),
                    "num_successful_canaries": num_successful_canaries,
                    "num_failed_canaries": num_failed_canaries,
                    "responses": responses,
                },
            }
        ),
    }
