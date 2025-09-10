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
        LOG.info(f"Getting workflow for event:\n{json.dumps(event, indent=4)}")
        workflow = Workflows.from_string(event["workflow_name"])

        match workflow:
            case Workflows.UPDATE_SECURITY_PRICES:
                return UpdateSecurityPrices(DOMAIN, DATABASE, POLYGON, DATADOG)
            case Workflows.SYNC_USER_TRANSACTIONS:
                return SyncUserTransactions(DOMAIN, PLAID, DATABASE, DATADOG)
            case _:
                raise ValueError(f"Workflow '{workflow}' not found")
