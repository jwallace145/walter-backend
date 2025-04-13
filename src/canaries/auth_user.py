from dataclasses import dataclass

import requests
from requests import Response

from src.canaries.common.canary import BaseCanary
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class AuthUserCanary(BaseCanary):
    """
    WalterCanary: AuthUserCanary

    This canary calls the AuthUser API and ensures
    the canary user is able to authenticate successfully.
    """

    CANARY_NAME = "AuthUserCanary"
    API_URL = "https://084slq55lk.execute-api.us-east-1.amazonaws.com/dev/auth"
    USER_EMAIL = "canary@walterai.dev"
    USER_PASSWORD = "CanaryPassword1234&"

    def __init__(self) -> None:
        super().__init__(
            AuthUserCanary.CANARY_NAME,
            AuthUserCanary.API_URL,
        )

    def call_api(self) -> Response:
        return requests.post(
            url=AuthUserCanary.API_URL,
            json={
                "email": AuthUserCanary.USER_EMAIL,
                "password": AuthUserCanary.USER_PASSWORD,
            },
            headers={"content-type": "application/json"},
        )
