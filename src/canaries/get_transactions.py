from dataclasses import dataclass

import requests
from requests import Response
from datetime import datetime

from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.canaries.common.canary import BaseCanary
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class GetTransactionsCanary(BaseCanary):
    """
    WalterCanary: GetTransactionsCanary

    This canary calls the GetExpenses API to ensure
    that users can get their expenses from WalterDB
    successfully.
    """

    CANARY_NAME = "GetTransactionsCanary"
    API_URL = "https://084slq55lk.execute-api.us-east-1.amazonaws.com/dev/transactions"
    USER_EMAIL = "canary@walterai.dev"

    authenticator: WalterAuthenticator

    def __init__(
        self, authenticator: WalterAuthenticator, metrics: WalterCloudWatchClient
    ) -> None:
        super().__init__(
            GetTransactionsCanary.CANARY_NAME, GetTransactionsCanary.API_URL, metrics
        )
        self.authenticator = authenticator

    def call_api(self) -> Response:
        token = self.authenticator.generate_user_token(GetTransactionsCanary.USER_EMAIL)
        today = datetime.today()
        first_day_of_current_month = today.replace(day=1).strftime("%Y-%m-%d")
        current_date = today.strftime("%Y-%m-%d")
        return requests.get(
            url=GetTransactionsCanary.API_URL,
            headers={
                "Authorization": f"Bearer {token}",
            },
            params={
                "start_date": first_day_of_current_month,
                "end_date": current_date,
            },
        )
