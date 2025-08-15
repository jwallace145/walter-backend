from src.api.routing.router import APIRouter
from src.canaries.routing.router import CanaryRouter, CanaryType
from src.workflows.common.router import WorkflowRouter


def walter_api_entrypoint(event, context) -> dict:
    return APIRouter.get_method(event).invoke(event).to_json()


def walter_workflows_entrypoint(event, context) -> dict:
    return WorkflowRouter.get_workflow(event).invoke(event).to_json()


def walter_canaries_entrypoint(event, context) -> None:
    for canary in CanaryType:
        name = canary.value
        CanaryRouter.get_canary({"canary": name}).invoke()
