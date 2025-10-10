from dataclasses import dataclass
from typing import Optional

import requests
from requests import Response
from requests.cookies import RequestsCookieJar

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
        api_key: str,
        authenticator: WalterAuthenticator,
        db: WalterDB,
        metrics: DatadogMetricsClient,
    ) -> None:
        super().__init__(
            Logout.API_NAME, Logout.API_URL, api_key, authenticator, db, metrics
        )

    def is_authenticated(self) -> bool:
        return True

    def call_api(self, tokens: Optional[Tokens] = None) -> Response:
        return requests.post(
            Logout.API_URL,
            headers={
                "Authorization": f"Bearer {tokens.access_token}",
                "x-api-key": self.api_key,
            },
        )

    def validate_cookies(self, cookies: RequestsCookieJar) -> None:
        required_cookies = []
        self._validate_required_response_cookies(cookies, required_cookies)

    def validate_data(self, data: dict) -> None:
        required_fields = [
            ("user_id", None),
            ("session_id", None),
            ("session_start", None),
            ("session_end", None),
        ]
        self._validate_required_response_data_fields(data, required_fields)

    def clean_up(self) -> None:
        LOG.info(f"No resources to clean up after '{self.API_NAME}' canary!")
