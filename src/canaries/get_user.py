from dataclasses import dataclass

import requests
from requests import Response

from src.auth.authenticator import WalterAuthenticator
from src.canaries.common.canary import BaseCanary
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class GetUserCanary(BaseCanary):
    """
    WalterCanary: GetUserCanary

    This canary calls the GetUser API and ensures
    that Walter can verify authenticated users
    identity successfully.
    """

    CANARY_NAME = "GetUserCanary"
    API_URL = "https://084slq55lk.execute-api.us-east-1.amazonaws.com/dev/users"
    USER_EMAIL = "canary@walterai.dev"

    authenticator: WalterAuthenticator

    def __init__(self, authenticator: WalterAuthenticator) -> None:
        super().__init__(GetUserCanary.CANARY_NAME, GetUserCanary.API_URL)
        self.authenticator = authenticator

    def call_api(self) -> Response:
        token = self.authenticator.generate_user_token(email=GetUserCanary.USER_EMAIL)
        return requests.get(
            GetUserCanary.API_URL,
            headers={"Authorization": f"Bearer {token}"},
        )
