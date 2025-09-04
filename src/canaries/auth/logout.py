from dataclasses import dataclass
from typing import Optional

import requests
from requests import Response

from src.auth.authenticator import WalterAuthenticator
from src.auth.models import Tokens
from src.canaries.common.canary import BaseCanary
from src.database.client import WalterDB
from src.metrics.client import DatadogMetricsClient
from src.utils.log import Logger

LOG = Logger(__name__).get_logger()


@dataclass
class Logout(BaseCanary):
    """Login API Canary"""

    API_NAME = "Logout"
    API_URL = f"{BaseCanary.CANARY_ENDPOINT}/auth/logout"

    def __init__(
        self,
        authenticator: WalterAuthenticator,
        db: WalterDB,
        metrics: DatadogMetricsClient,
    ) -> None:
        super().__init__(Logout.API_NAME, Logout.API_URL, authenticator, db, metrics)

    def is_authenticated(self) -> bool:
        return True

    def call_api(self, tokens: Optional[Tokens] = None) -> Response:
        return requests.post(
            Logout.API_URL,
            headers={"Authorization": f"Bearer {tokens.access_token}"},
        )

    def validate_data(self, response: dict) -> None:
        pass

    def clean_up(self) -> None:
        LOG.info(f"No resources to clean up after '{self.API_NAME}' canary!")
