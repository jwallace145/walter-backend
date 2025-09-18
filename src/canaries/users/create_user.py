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
class CreateUser(BaseCanary):
    """
    Canary: CreateUser

    This canary calls the CreateUser API and ensures
    that new users can onboard successfully.
    """

    CANARY_NAME = "CreateUser"
    API_URL = f"{BaseCanary.CANARY_ENDPOINT}/users"

    NEW_USER_EMAIL = "newuser@walterai.dev"
    NEW_USER_FIRST_NAME = "New"
    NEW_USER_LAST_NAME = "User"
    NEW_USER_PASSWORD = "P@ssw0rd1234!"

    def __init__(
        self,
        authenticator: WalterAuthenticator,
        db: WalterDB,
        metrics: DatadogMetricsClient,
    ) -> None:
        super().__init__(
            CreateUser.CANARY_NAME, CreateUser.API_URL, authenticator, db, metrics
        )

    def is_authenticated(self) -> bool:
        return False

    def call_api(self, tokens: Optional[Tokens] = None) -> Response:
        return requests.post(
            CreateUser.API_URL,
            headers={"Content-Type": "application/json"},
            json={
                "email": self.NEW_USER_EMAIL,
                "first_name": self.NEW_USER_FIRST_NAME,
                "last_name": self.NEW_USER_LAST_NAME,
                "password": self.NEW_USER_PASSWORD,
            },
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
            ("sign_up_date", None),
            ("verified", None),
        ]
        self._validate_required_response_data_fields(response, required_fields)

    def clean_up(self) -> None:
        LOG.info(f"Cleaning up after '{self.CANARY_NAME}' canary!")

        # attempt to get new user from database after canary
        new_user = self.db.get_user_by_email(self.NEW_USER_EMAIL)

        # if user exists, delete user from database, else skip cleanup
        if not new_user:
            LOG.info(f"User '{self.NEW_USER_EMAIL}' does not exist, skipping cleanup!")
        else:
            LOG.info(f"Deleting user '{self.NEW_USER_EMAIL}' from database")
            self.db.delete_user(new_user.user_id)
