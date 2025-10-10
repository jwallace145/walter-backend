import os
from dataclasses import dataclass

from src.canaries.common.canary import BaseCanary
from src.canaries.factory import CanaryFactory, CanaryType
from src.environment import AWS_REGION, DOMAIN
from src.factory import ClientFactory
from src.utils.log import Logger

log = Logger(__name__).get_logger()

WALTER_BACKEND_API_KEY = os.getenv("WALTER_BACKEND_API_KEY", None)
"""(str): The API key used to authenticate client requests with the WalterBackend API."""


@dataclass
class CanaryRouter:
    """Router for Canaries"""

    # set during post-init
    client_factory: ClientFactory = None
    canary_factory: CanaryFactory = None

    def __post_init__(self) -> None:
        log.debug("Initializing CanaryRouter")
        self.client_factory = ClientFactory(region=AWS_REGION, domain=DOMAIN)
        self.canary_factory = CanaryFactory(
            client_factory=self.client_factory, api_key=WALTER_BACKEND_API_KEY
        )

    def get_canary(self, canary_type: CanaryType) -> BaseCanary:
        log.info(f"Getting '{canary_type.value}' canary'")
        return self.canary_factory.get_canary(canary_type)
