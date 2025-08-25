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
class Login(BaseCanary):
    """Login API Canary"""

    API_NAME = "Login"
    API_URL = "https://084slq55lk.execute-api.us-east-1.amazonaws.com/dev/auth/login"

    def __init__(
        self,
        authenticator: WalterAuthenticator,
        db: WalterDB,
        metrics: DatadogMetricsClient,
    ) -> None:
        super().__init__(Login.API_NAME, Login.API_URL, authenticator, db, metrics)

    def is_authenticated(self) -> bool:
        return False

    def call_api(self, tokens: Optional[Tokens] = None) -> Response:
        return requests.post(
            Login.API_URL,
            headers={"Content-Type": "application/json"},
            json={
                "email": self.CANARY_USER_EMAIL,
                "password": self.CANARY_USER_PASSWORD + "INVALID",
            },
        )

    def validate_data(self, response: dict) -> None:
        # validate required fields in response data
        required_fields = [
            "user_id",
            "refresh_token",
            "access_token",
            "refresh_token_expires_at",
            "access_token_expires_at",
        ]
        self._validate_required_response_data_fields(response, required_fields)
