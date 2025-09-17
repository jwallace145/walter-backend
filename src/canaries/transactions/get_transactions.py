from dataclasses import dataclass
from typing import Optional

import requests
from requests import Response

from src.auth.authenticator import WalterAuthenticator
from src.auth.models import Tokens
from src.canaries.common.canary import BaseCanary
from src.canaries.common.exceptions import CanaryFailure
from src.database.client import WalterDB
from src.metrics.client import DatadogMetricsClient
from src.utils.log import Logger

LOG = Logger(__name__).get_logger()


@dataclass
class GetTransactions(BaseCanary):
    """
    WalterBackend-Canary: GetTransactions

    This canary calls the GetTransactions API and ensures the
    user transactions are retrieved successfully.
    """

    CANARY_NAME = "GetTransactions"
    API_URL = f"{BaseCanary.CANARY_ENDPOINT}/transactions"

    def __init__(
        self,
        authenticator: WalterAuthenticator,
        db: WalterDB,
        metrics: DatadogMetricsClient,
    ) -> None:
        super().__init__(
            GetTransactions.CANARY_NAME,
            GetTransactions.API_URL,
            authenticator,
            db,
            metrics,
        )

    def is_authenticated(self) -> bool:
        return True

    def call_api(self, tokens: Optional[Tokens] = None) -> Response:
        return requests.get(
            GetTransactions.API_URL,
            headers={"Authorization": f"Bearer {tokens.access_token}"},
        )

    def validate_cookies(self, response: dict) -> None:
        self._validate_required_response_cookies(response, [])

    def validate_data(self, response: dict) -> None:
        # canary transaction details
        expected_num_transactions = 3
        expected_total_income = 00.00
        expected_total_expense = 105.00
        expected_cash_flow = -105.00

        # validate response data exists and is valid
        data = BaseCanary.validate_response_data(response)
        for field, value in {
            "user_id": None,
            "num_transactions": expected_num_transactions,
            "total_income": expected_total_income,
            "total_expense": expected_total_expense,
            "cash_flow": expected_cash_flow,
            "transactions": None,
        }.items():
            BaseCanary.validate_required_field(data, field, value)

        # assert expected number of transactions are returned
        transactions = data["transactions"]
        if len(transactions) != expected_num_transactions:
            raise CanaryFailure(
                f"Expected {expected_num_transactions} transactions in response!"
            )

        # assert transactions returned in response are valid in format
        for transaction in transactions:
            for field in [
                "account_id",
                "transaction_id",
                "transaction_date",
                "transaction_type",
                "transaction_subtype",
                "transaction_category",
                "transaction_amount",
            ]:
                BaseCanary.validate_required_field(transaction, field)

    def clean_up(self) -> None:
        LOG.info(f"No resources to clean up after '{self.CANARY_NAME}' canary!")
