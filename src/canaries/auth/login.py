import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import requests
from requests import Response
from requests.cookies import RequestsCookieJar

from src.api.common.exceptions import SessionDoesNotExist
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
    API_URL = f"{BaseCanary.CANARY_ENDPOINT}/auth/login"

    def __init__(
        self,
        api_key: str,
        authenticator: WalterAuthenticator,
        db: WalterDB,
        metrics: DatadogMetricsClient,
    ) -> None:
        super().__init__(
            Login.API_NAME, Login.API_URL, api_key, authenticator, db, metrics
        )

    def is_authenticated(self) -> bool:
        return False

    def call_api(self, tokens: Optional[Tokens] = None) -> Response:
        api_response = requests.post(
            Login.API_URL,
            headers={"Content-Type": "application/json", "x-api-key": self.api_key},
            json={
                "email": self.CANARY_USER_EMAIL,
                "password": self.CANARY_USER_PASSWORD,
            },
        )

        LOG.info("Logging out canary after successful Login API call...")

        # get access token from cookies
        access_token = None
        cookies: RequestsCookieJar = api_response.cookies
        for cookie in cookies:
            if cookie.name == "WALTER_BACKEND_ACCESS_TOKEN":
                access_token = cookie.value

        user_id, session_id = self.authenticator.decode_access_token(access_token)

        LOG.info(
            f"Getting session for user '{user_id}' with session ID '{session_id}'..."
        )
        session = self.db.get_session(user_id, session_id)
        if not session:
            LOG.error(f"Session '{session_id}' not found for user '{user_id}'!")
            raise SessionDoesNotExist("Session does not exist!")

        LOG.info(
            f"Revoking session for user '{user_id}' with session ID '{session_id}'..."
        )
        session.revoked = True
        session.session_end = datetime.now(timezone.utc)
        session.ttl = int(
            time.time()
        )  # immediately expire canary session to reduce num db entries
        self.db.update_session(session)

        return api_response

    def validate_cookies(self, cookies: RequestsCookieJar) -> None:
        # validate required cookies in response
        required_cookies = [
            "WALTER_BACKEND_ACCESS_TOKEN",
            "WALTER_BACKEND_REFRESH_TOKEN",
        ]
        self._validate_required_response_cookies(cookies, required_cookies)

    def validate_data(self, data: dict) -> None:
        # validate required fields in response data
        required_fields = [
            ("user_id", None),
            ("access_token_expires_at", None),
            ("refresh_token_expires_at", None),
        ]
        self._validate_required_response_data_fields(data, required_fields)

    def clean_up(self) -> None:
        LOG.info(f"No resources to clean up after '{self.API_NAME}' canary!")
