import datetime
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
from src.database.transactions.models import Transaction, TransactionCategory
from src.metrics.client import DatadogMetricsClient
from src.utils.log import Logger

LOG = Logger(__name__).get_logger()


@dataclass
class UpdateTransaction(BaseCanary):
    """
    WalterBackend Canary: UpdateTransaction
    """

    CANARY_NAME = "UpdateTransaction"
    API_URL = f"{BaseCanary.CANARY_ENDPOINT}/transactions"

    def __init__(
        self,
        api_key: str,
        authenticator: WalterAuthenticator,
        db: WalterDB,
        metrics: DatadogMetricsClient,
    ) -> None:
        super().__init__(
            UpdateTransaction.CANARY_NAME,
            UpdateTransaction.API_URL,
            api_key,
            authenticator,
            db,
            metrics,
        )

    def is_authenticated(self) -> bool:
        return True

    def call_api(self, tokens: Optional[Tokens] = None) -> Response:
        return requests.put(
            UpdateTransaction.API_URL,
            headers={
                "x-api-key": self.api_key,
                "Authorization": f"Bearer {tokens.access_token}",
                "Content-Type": "application/json",
            },
            json={
                "transaction_date": "2025-08-01",
                "transaction_id": "bank-txn-7015884840",  # TODO: parameterize this by environment
                "updated_merchant_name": "Canary Coffee",
                "updated_category": "Entertainment",  # originally "Restaurants"
            },
        )

    def validate_cookies(self, cookies: RequestsCookieJar) -> None:
        required_cookies = []
        self._validate_required_response_cookies(cookies, required_cookies)

    def validate_data(self, data: dict) -> None:
        # update transaction api returns a single transaction object
        required_fields = [("transaction", None)]
        self._validate_required_response_data_fields(data, required_fields)

        # index into returned transaction and validate required fields
        transaction: dict = data["Data"]["transaction"]
        required_fields = [
            ("user_id", None),
            ("account_id", None),
            ("transaction_id", None),
            ("transaction_date", None),
            ("merchant_name", None),
            ("transaction_amount", None),
            ("transaction_category", None),
            ("transaction_type", None),
            ("transaction_subtype", None),
            ("merchant_logo_s3_uri", None),
        ]
        self._validate_required_response_data_fields(transaction, required_fields)

    def clean_up(self) -> None:
        LOG.info(
            f"Reverting updated transaction to its original state after '{self.CANARY_NAME}' canary..."
        )

        # canary transaction details
        account_id = "acct-5782898837"
        transaction_id = "bank-txn-7015884840"
        transaction_date = datetime.datetime.strptime("2025-08-01", "%Y-%m-%d")

        # get original transaction from database
        LOG.debug("Getting original transaction...")
        transaction: Optional[Transaction] = self.db.get_transaction(
            account_id=account_id,
            transaction_id=transaction_id,
            transaction_date=transaction_date,
        )

        # verify that the original transaction exists, otherwise raise an exception
        if transaction is None:
            raise CanaryFailure(
                f"Original transaction not found for account '{account_id}' and transaction '{transaction_id}'!"
            )

        LOG.debug("Original transaction found! Reverting to original state...")
        transaction.transaction_category = TransactionCategory.RESTAURANTS
        self.db.update_transaction(transaction)

        LOG.info(
            f"Successfully reverted changes made to the original transaction for '{self.CANARY_NAME}' canary!"
        )
