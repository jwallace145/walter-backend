from dataclasses import dataclass

from src.utils.log import Logger
from src.workflows.common.models import Workflow
from src.workflows.update_security_prices import UpdateSecurityPrices
from src.workflows.workflows import update_security_prices_workflow

log = Logger(__name__).get_logger()


@dataclass
class WorkflowRouter:
    """Workflow Router"""

    @staticmethod
    def get_workflow(event: dict) -> Workflow:
        workflow_name = event["workflow_name"]
        match workflow_name:
            case UpdateSecurityPrices.WORKFLOW_NAME:
                return update_security_prices_workflow
            case _:
                raise ValueError(f"Workflow '{workflow_name}' not found")
