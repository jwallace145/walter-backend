import json
from dataclasses import dataclass
from enum import Enum

from src.clients import DATABASE, DATADOG, DOMAIN, PLAID, POLYGON
from src.utils.log import Logger
from src.workflows.common.models import Workflow
from src.workflows.sync_user_transactions import SyncUserTransactions
from src.workflows.update_security_prices import UpdateSecurityPrices

LOG = Logger(__name__).get_logger()


class Workflows(Enum):
    """Workflows"""

    SYNC_USER_TRANSACTIONS = SyncUserTransactions.WORKFLOW_NAME
    UPDATE_SECURITY_PRICES = UpdateSecurityPrices.WORKFLOW_NAME

    @classmethod
    def from_string(cls, workflow: str):
        for workflow_enum in Workflows:
            if workflow_enum.value.lower() == workflow.lower():
                return workflow_enum
        raise ValueError(f"{workflow} is not a valid workflow!")


@dataclass
class WorkflowRouter:
    """Workflow Router"""

    @staticmethod
    def get_workflow(event: dict) -> Workflow:
        workflow_name = WorkflowRouter._get_workflow_name(event)
        workflow = Workflows.from_string(workflow_name)

        match workflow:
            case Workflows.UPDATE_SECURITY_PRICES:
                return UpdateSecurityPrices(DOMAIN, DATABASE, POLYGON, DATADOG)
            case Workflows.SYNC_USER_TRANSACTIONS:
                return SyncUserTransactions(DOMAIN, PLAID, DATABASE, DATADOG)
            case _:
                raise ValueError(f"Workflow '{workflow}' not found")

    @staticmethod
    def _get_workflow_name(event: dict) -> str:
        LOG.info(f"Getting workflow name from event:\n{json.dumps(event, indent=4)}")

        # only sqs messages have records in the event
        # so if there are no records, assume its a scheduled job
        # where workflow_name is in the event
        if "Records" not in event:
            if "workflow_name" in event:
                return event["workflow_name"]
            else:
                raise ValueError("No workflow name found in event!")

        # if records exist, assume its an sqs message and parse
        # accordingly
        try:
            records = event["Records"]

            if len(records) == 0:
                raise ValueError("No records found in event!")

            if len(records) > 1:
                raise ValueError("More than one record found in event!")

            record = records[0]
            body = json.loads(record["body"])
            workflow_name = body["workflow_name"]
            return workflow_name
        except Exception as e:
            raise ValueError(f"Failed to get workflow name from event: {e}")
