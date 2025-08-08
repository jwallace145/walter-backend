from src.api.routing.router import APIRouter
from src.canaries.routing.router import CanaryRouter, CanaryType


def walter_api_entrypoint(event, context) -> dict:
    return APIRouter.get_method(event).invoke(event).to_json()

  
def walter_canaries_entrypoint(event, context) -> None:
    for canary in CanaryType:
        name = canary.value
        CanaryRouter.get_canary({"canary": name}).invoke()

