from dataclasses import dataclass

import requests
from requests import Response

from src.auth.authenticator import WalterAuthenticator
from src.canaries.common.canary import BaseCanary
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class GetPortfolioCanary(BaseCanary):
    """
    WalterCanary: GetPortfolioCanary

    This canary calls the GetPortfolio API and
    verifies that users can successfully retrieve
    their portfolio from the database.
    """

    CANARY_NAME = "GetPortfolioCanary"
    API_URL = "https://084slq55lk.execute-api.us-east-1.amazonaws.com/dev/portfolios"
    USER_EMAIL = "canary@walterai.dev"

    authenticator: WalterAuthenticator

    def __init__(self, authenticator: WalterAuthenticator) -> None:
        super().__init__(
            GetPortfolioCanary.CANARY_NAME,
            GetPortfolioCanary.API_URL,
        )
        self.authenticator = authenticator

    def call_api(self) -> Response:
        token = self.authenticator.generate_user_token(
            email=GetPortfolioCanary.USER_EMAIL
        )
        return requests.get(
            url=GetPortfolioCanary.API_URL,
            headers={"Authorization": f"Bearer {token}"},
        )
