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
class Refresh(BaseCanary):
    """Refresh API Canary"""

    API_NAME = "Refresh"
    API_URL = "https://084slq55lk.execute-api.us-east-1.amazonaws.com/dev/auth/refresh"

    def __init__(
        self,
        authenticator: WalterAuthenticator,
        db: WalterDB,
        metrics: DatadogMetricsClient,
    ) -> None:
        super().__init__(Refresh.API_NAME, Refresh.API_URL, authenticator, db, metrics)

    def is_authenticated(self) -> bool:
        return True

    def call_api(self, tokens: Optional[Tokens] = None) -> Response:
        return requests.post(
            Refresh.API_URL, headers={"Authorization": f"Bearer {tokens.refresh_token}"}
        )

    def validate_data(self, response: dict) -> None:
        # validate required fields in response data
        required_fields = ["access_token", "access_token_expiration"]
        self._validate_required_response_data_fields(response, required_fields)
