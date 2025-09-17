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
class GetUser(BaseCanary):
    """
    WalterCanary: GetUser

    This canary calls the GetUser API and ensures
    that Walter can verify authenticated users
    identity successfully.
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
            GetUser.CANARY_NAME, GetUser.API_URL, authenticator, db, metrics
        )

    def is_authenticated(self) -> bool:
        return True

    def call_api(self, tokens: Optional[Tokens] = None) -> Response:
        return requests.get(
            GetUser.API_URL,
            headers={"Authorization": f"Bearer {tokens.access_token}"},
        )

    def validate_cookies(self, cookies: RequestsCookieJar) -> None:
        required_cookies = []
        self._validate_required_response_cookies(cookies, required_cookies)

    def validate_data(self, response: dict) -> None:
        required_fields = [
            ("user_id", None),
            ("email", None),
            ("first_name", None),
            ("last_name", None),
            ("verified", None),
            ("sign_up_date", None),
            ("last_active_date", None),
            ("profile_picture_url", None),
            ("active_stripe_subscription", None),
        ]
        self._validate_required_response_data_fields(response, required_fields)

    def clean_up(self) -> None:
        LOG.info(f"No resources to clean up after '{self.CANARY_NAME}' canary!")
