from src.canaries.routing.router import CanaryRouter
from src.factory import CLIENT_FACTORY

CANARY_ROUTER: CanaryRouter = CanaryRouter(client_factory=CLIENT_FACTORY)
"""(CanaryRouter): The canary router used to route canary requests to the appropriate canary execution method."""
