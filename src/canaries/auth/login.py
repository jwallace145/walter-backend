import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import requests
from requests import Response

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
        api_response = requests.post(
            Login.API_URL,
            headers={"Content-Type": "application/json"},
            json={
                "email": self.CANARY_USER_EMAIL,
                "password": self.CANARY_USER_PASSWORD,
            },
        )

        LOG.info("Logging out canary after successful Login API call...")
        response = api_response.json()
        access_token = response["Data"]["access_token"]
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
