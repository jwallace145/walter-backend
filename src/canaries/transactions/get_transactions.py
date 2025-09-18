from dataclasses import dataclass
from typing import Optional

import requests
from requests import Response
from requests.cookies import RequestsCookieJar

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

    def validate_cookies(self, cookies: RequestsCookieJar) -> None:
        required_cookies = []
        self._validate_required_response_cookies(cookies, required_cookies)

    def validate_data(self, data: dict) -> None:
        # canary transaction details
        expected_num_transactions = 3
        expected_total_income = 00.00
        expected_total_expense = 105.00
        expected_cash_flow = -105.00

        required_fields = [
            ("user_id", None),
            ("num_transactions", expected_num_transactions),
            ("total_income", expected_total_income),
            ("total_expense", expected_total_expense),
            ("cash_flow", expected_cash_flow),
            ("transactions", None),
        ]
        self._validate_required_response_data_fields(data, required_fields)

        # assert expected number of transactions are returned
        transactions = data["Data"]["transactions"]
        if len(transactions) != expected_num_transactions:
            raise CanaryFailure(
                f"Expected {expected_num_transactions} transactions in response!"
            )

        required_transactions = {
            "bank-txn-7015884840": [
                ("account_id", "acct-5782898837"),
                ("transaction_id", "bank-txn-7015884840"),
                ("account_institution_name", "Canary Bank"),
                ("account_name", "Canary Credit Account"),
                ("account_type", "credit"),
                ("account_mask", "2222"),
                ("transaction_type", "banking"),
                ("transaction_subtype", "debit"),
                ("transaction_category", "Restaurants"),
                ("transaction_date", "2025-08-01"),
                ("merchant_name", "Canary Coffee"),
                ("transaction_amount", 5.0),
            ],
            "bank-txn-7016361254": [
                ("account_id", "acct-5782898837"),
                ("transaction_id", "bank-txn-7016361254"),
                ("account_institution_name", "Canary Bank"),
                ("account_name", "Canary Credit Account"),
                ("account_type", "credit"),
                ("account_mask", "2222"),
                ("transaction_type", "banking"),
                ("transaction_subtype", "debit"),
                ("transaction_category", "Entertainment"),
                ("transaction_date", "2025-08-01"),
                ("merchant_name", "Canary Concert Tickets"),
                ("transaction_amount", 100.0),
            ],
            "investment-txn-7017568759": [
                ("account_id", "acct-5782388299"),
                ("transaction_id", "investment-txn-7017568759"),
                ("security_id", "sec-nasdaq-amzn"),
                ("account_institution_name", "Canary Investing"),
                ("account_name", "Canary Retirement Account"),
                ("account_type", "investment"),
                ("account_mask", "1111"),
                ("transaction_date", "2025-08-01"),
                ("transaction_type", "investment"),
                ("transaction_subtype", "buy"),
                ("transaction_category", "Investment"),
                ("price_per_share", 100.0),
                ("quantity", 10.0),
                ("transaction_amount", 1000.0),
            ],
        }

        for transaction in transactions:
            if "transaction_id" not in transaction:
                raise CanaryFailure(
                    f"Missing 'transaction_id' in transaction: {transaction}"
                )

            if transaction["transaction_id"] not in required_transactions:
                raise CanaryFailure(
                    f"Unexpected transaction returned in response: {transaction}"
                )

            expected_transaction = required_transactions[transaction["transaction_id"]]
            self._validate_required_response_data_fields(
                transaction, expected_transaction
            )

    def clean_up(self) -> None:
        LOG.info(f"No resources to clean up after '{self.CANARY_NAME}' canary!")
