import json
from dataclasses import dataclass

from src.environment import AWS_REGION, DOMAIN
from src.factory import ClientFactory
from src.utils.log import Logger
from src.workflows.common.models import Workflow
from src.workflows.factory import WorkflowFactory, Workflows

LOG = Logger(__name__).get_logger()


@dataclass(kw_only=True)
class WorkflowRouter:
    """Router for WalterBackend workflows."""

    # set during post-init
    client_factory: ClientFactory = None
    workflow_factory: WorkflowFactory = None

    def __post_init__(self) -> None:
        LOG.debug("Initializing WorkflowRouter")
        self.client_factory = ClientFactory(region=AWS_REGION, domain=DOMAIN)
        self.workflow_factory = WorkflowFactory(client_factory=self.client_factory)

    def get_workflow(self, event: dict) -> Workflow:
        workflow_name = self._get_workflow_name(event)
        workflow = Workflows.from_string(workflow_name)
        return self.workflow_factory.get_workflow(workflow)

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
