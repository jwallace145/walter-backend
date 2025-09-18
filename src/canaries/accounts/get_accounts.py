from dataclasses import dataclass
from typing import Optional

import requests
from requests import Response
from requests.cookies import RequestsCookieJar

from src.auth.authenticator import WalterAuthenticator
from src.auth.models import Tokens
from src.canaries.common.canary import BaseCanary
from src.canaries.common.exceptions import CanaryFailure
from src.database.accounts.models import AccountType
from src.database.client import WalterDB
from src.metrics.client import DatadogMetricsClient
from src.utils.log import Logger

LOG = Logger(__name__).get_logger()


@dataclass
class GetAccounts(BaseCanary):
    """
    WalterCanary: GetAccounts
    """

    CANARY_NAME = "GetAccounts"
    API_URL = f"{BaseCanary.CANARY_ENDPOINT}/accounts"

    def __init__(
        self,
        authenticator: WalterAuthenticator,
        db: WalterDB,
        metrics: DatadogMetricsClient,
    ) -> None:
        super().__init__(
            GetAccounts.CANARY_NAME, GetAccounts.API_URL, authenticator, db, metrics
        )

    def is_authenticated(self) -> bool:
        return True

    def call_api(self, tokens: Optional[Tokens] = None) -> Response:
        return requests.get(
            GetAccounts.API_URL,
            headers={"Authorization": f"Bearer {tokens.access_token}"},
        )

    def validate_cookies(self, cookies: RequestsCookieJar) -> None:
        required_cookies = []
        self._validate_required_response_cookies(cookies, required_cookies)

    def validate_data(self, data: dict) -> None:
        required_fields = [
            ("user_id", None),
            ("total_num_accounts", None),
            ("total_balance", None),
            ("accounts", None),
        ]
        self._validate_required_response_data_fields(data, required_fields)

        # validate required fields in accounts response data
        for account in data["Data"]["accounts"]:
            account_type = None
            try:
                account_type = AccountType.from_string(account["account_type"])
            except Exception:
                raise CanaryFailure(
                    f"Invalid account type '{account['account_type']}'!"
                )

            # get required account fields by account type
            required_account_fields = []
            match account_type:
                case AccountType.DEPOSITORY | AccountType.CREDIT | AccountType.LOAN:
                    required_account_fields = [
                        ("account_id", None),
                        ("institution_name", None),
                        ("account_name", None),
                        ("account_type", None),
                        ("account_subtype", None),
                        ("balance", None),
                        ("updated_at", None),
                    ]
                case AccountType.INVESTMENT:
                    required_account_fields = [
                        ("account_id", None),
                        ("institution_name", None),
                        ("account_name", None),
                        ("account_type", None),
                        ("account_subtype", None),
                        ("balance", None),
                        ("updated_at", None),
                        ("holdings", None),
                    ]

            # validate required fields in account response data
            self._validate_required_response_data_fields(
                account, required_account_fields
            )

    def clean_up(self) -> None:
        LOG.info(f"No resources to clean up after '{self.CANARY_NAME}' canary!")
