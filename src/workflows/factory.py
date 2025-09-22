from dataclasses import dataclass
from enum import Enum
from typing import Tuple

from src.aws.sts.client import WalterSTSClient
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

    def get_name(self) -> str:
        return self.value

    @classmethod
    def from_string(cls, workflow: str):
        for workflow_enum in Workflows:
            if workflow_enum.value.lower() == workflow.lower():
                return workflow_enum
        raise ValueError(f"{workflow} is not a valid workflow!")


@dataclass(kw_only=True)
class WorkflowFactory:

    # This must stay in sync with the role name format in Terraform
    WORKFLOW_ROLE_NAME_FORMAT = "WalterBackend-Workflow-{workflow}-Role-{domain}"

    client_factory: ClientFactory

    def __post_init__(self) -> None:
        LOG.debug("Creating WorkflowFactory")

    def get_workflow(self, workflow: Workflows, request_id: str) -> Workflow:
        LOG.info(f"Getting workflow '{workflow.value}' for request '{request_id}'")

        # get workflow specific credentials
        workflow_credentials: Tuple[str, str, str] = self.get_workflow_credentials(
            workflow, request_id
        )
        aws_access_key_id, aws_secret_access_key, aws_session_token = (
            workflow_credentials
        )

        # set client factory workflow credentials to create boto3 clients with
        # correctly scoped credentials
        self.client_factory.set_aws_credentials(
            aws_access_key_id, aws_secret_access_key, aws_session_token
        )

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

    def get_workflow_credentials(
        self, workflow: Workflows, request_id: str
    ) -> Tuple[str, str, str]:
        LOG.info(f"Getting workflow credentials for '{workflow.value}'")
        domain: str = self.client_factory.get_domain().value

        role_name = self.WORKFLOW_ROLE_NAME_FORMAT.format(
            workflow=workflow.get_name(), domain=domain
        )

        LOG.info(f"Assuming role '{role_name}'")
        sts: WalterSTSClient = self.client_factory.get_sts_client()
        credentials = sts.assume_role(
            role_name,
            request_id,
        )
        LOG.info(f"Assumed role '{role_name}' successfully!")

        # get credentials from assume role response api call
        aws_access_key_id = credentials["AccessKeyId"]
        aws_secret_access_key = credentials["SecretAccessKey"]
        aws_session_token = credentials["SessionToken"]

        # return assumed role credentials
        return aws_access_key_id, aws_secret_access_key, aws_session_token
