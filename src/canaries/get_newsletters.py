from dataclasses import dataclass

import requests
from requests import Response

from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.canaries.common.canary import BaseCanary
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class GetNewslettersCanary(BaseCanary):
    """
    WalterCanary: GetNewsletters

    This canary calls the GetNewsletters API and ensures
    users are able to get a list of their newsletters.
    """

    CANARY_NAME = "GetNewslettersCanary"
    API_URL = "https://084slq55lk.execute-api.us-east-1.amazonaws.com/dev/newsletters"
    USER_EMAIL = "canary@walterai.dev"

    authenticator: WalterAuthenticator

    def __init__(
        self, authenticator: WalterAuthenticator, metrics: WalterCloudWatchClient
    ) -> None:
        super().__init__(
            GetNewslettersCanary.CANARY_NAME, GetNewslettersCanary.API_URL, metrics
        )
        self.authenticator = authenticator

    def call_api(self) -> Response:
        token = self.authenticator.generate_user_token(GetNewslettersCanary.USER_EMAIL)
        return requests.get(
            url=GetNewslettersCanary.API_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            params={"page": 1},
        )
