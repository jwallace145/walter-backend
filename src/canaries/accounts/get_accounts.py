from dataclasses import dataclass
from typing import Optional

import requests
from requests import Response

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

    def validate_data(self, response: dict) -> None:
        LOG.debug("Validating user email in API response data...")
        if response.get("Data", {}).get("user_id", None) is None:
            raise CanaryFailure("Missing user_id in API response")

        LOG.debug("Validating number of accounts in API response data...")
        if response.get("Data", {}).get("total_num_accounts", None) is None:
            raise CanaryFailure("Missing total_num_accounts in API response")

        LOG.debug("Validating total_balance in API response data...")
        if response.get("Data", {}).get("total_balance", None) is None:
            raise CanaryFailure("Missing total_balance in API response")

        LOG.debug("Validating accounts in API response data...")
        if response.get("Data", {}).get("accounts", None) is None:
            raise CanaryFailure("Missing accounts in API response")

        for account in response["Data"]["accounts"]:
            LOG.debug("Validating account")

            if account.get("account_id", None) is None:
                raise CanaryFailure("Missing account_id in API response")

            if account.get("institution_name", None) is None:
                raise CanaryFailure("Missing institution_name in API response")

            if account.get("account_name", None) is None:
                raise CanaryFailure("Missing account_name in API response")

            if account.get("account_type", None) is None:
                raise CanaryFailure("Missing account_type in API response")

            if (
                account["account_type"] == AccountType.INVESTMENT.value
                and account.get("holdings", None) is None
            ):
                raise CanaryFailure("Missing holdings in API response")

            if account.get("account_subtype", None) is None:
                raise CanaryFailure("Missing account_subtype in API response")

            if account.get("balance", None) is None:
                raise CanaryFailure("Missing balance in API response")

            LOG.debug("Validated account")
