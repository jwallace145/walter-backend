from dataclasses import dataclass

import requests

from src.api.common.models import Status
from src.auth.authenticator import WalterAuthenticator
from src.canaries.common.models import CanaryResponse
from src.utils.log import Logger
import datetime as dt

log = Logger(__name__).get_logger()


@dataclass
class GetPortfolioCanary:
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

    def __post_init__(self) -> None:
        log.debug(f"Initializing {GetPortfolioCanary.CANARY_NAME}")

    def invoke(self) -> dict:
        log.info(f"Invoked '{GetPortfolioCanary.CANARY_NAME}'!")

        start = dt.datetime.now(dt.UTC)

        token = self.authenticator.generate_user_token(
            email=GetPortfolioCanary.USER_EMAIL
        )
        response = requests.get(
            url=GetPortfolioCanary.API_URL,
            headers={"Authorization": f"Bearer {token}"},
        )

        end = dt.datetime.now(dt.UTC)

        log.info(
            f"API Response - Status Code: {response.status_code}, Response Body: {response.text}"
        )

        return CanaryResponse(
            canary_name=GetPortfolioCanary.CANARY_NAME,
            status=Status.SUCCESS if response.status_code == 200 else Status.FAILURE,
            response_time_millis=(end - start).total_seconds() * 1000,
        ).to_json()
