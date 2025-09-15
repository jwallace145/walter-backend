from src.factory import CLIENT_FACTORY
from src.workflows.common.router import WorkflowRouter

WORKFLOW_ROUTER: WorkflowRouter = WorkflowRouter(client_factory=CLIENT_FACTORY)
