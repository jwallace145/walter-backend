from dataclasses import dataclass
from typing import Optional

import requests
from requests import Response

from src.auth.authenticator import WalterAuthenticator
from src.auth.models import Tokens
from src.canaries.common.canary import BaseCanary
from src.canaries.common.exceptions import CanaryFailure
from src.database.client import WalterDB
from src.metrics.client import DatadogMetricsClient
from src.utils.log import Logger

LOG = Logger(__name__).get_logger()


@dataclass
class GetAccounts(BaseCanary):
    """
    WalterCanary: GetAccounts
    """

    CANARY_NAME = "GetUser"
    API_URL = f"{BaseCanary.CANARY_ENDPOINT}/users"

    def __init__(
        self,
        authenticator: WalterAuthenticator,
        db: WalterDB,
        metrics: DatadogMetricsClient,
    ) -> None:
        super().__init__(
            GetAccounts.CANARY_NAME, GetAccounts.API_URL, authenticator, db, metrics
        )

    def is_authenticated(self) -> bool:
        return True

    def call_api(self, tokens: Optional[Tokens] = None) -> Response:
        return requests.get(
            GetAccounts.API_URL,
            headers={"Authorization": f"Bearer {tokens.access_token}"},
        )

    def validate_data(self, response: dict) -> None:
        LOG.debug("Validating user email in API response data...")
        if response.get("Data", {}).get("email", None) is None:
            raise CanaryFailure("Missing user email in API response")

        email = response["Data"]["email"]
        if email != self.CANARY_USER_EMAIL:
            raise CanaryFailure(f"Unexpected user email in response: '{email}'")
        LOG.debug("Validated user email in API response data!")
