import json
from dataclasses import dataclass
from enum import Enum

from src.factory import ClientFactory
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


@dataclass(kw_only=True)
class WorkflowRouter:
    """Router for WalterBackend workflows."""

    client_factory: ClientFactory

    def __post_init__(self) -> None:
        LOG.debug("Initializing WorkflowRouter")

    def get_workflow(self, event: dict) -> Workflow:
        workflow_name = self._get_workflow_name(event)
        workflow = Workflows.from_string(workflow_name)

        match workflow:
            case Workflows.UPDATE_SECURITY_PRICES:
                return UpdateSecurityPrices(
                    domain=self.client_factory.get_domain(),
                    walter_db=self.client_factory.get_db_client(),
                    polygon=self.client_factory.get_polygon_client(),
                    metrics=self.client_factory.get_metrics_client(),
                )
            case Workflows.SYNC_USER_TRANSACTIONS:
                return SyncUserTransactions(
                    domain=self.client_factory.get_domain(),
                    plaid=self.client_factory.get_plaid_client(),
                    db=self.client_factory.get_db_client(),
                    metrics=self.client_factory.get_metrics_client(),
                )
            case _:
                raise ValueError(f"Workflow '{workflow}' not found")

    def _get_workflow_name(self, event: dict) -> str:
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
