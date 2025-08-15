from dataclasses import dataclass
from datetime import timezone, datetime, timedelta
from typing import List

from src.api.common.exceptions import NotAuthenticated, UserDoesNotExist, BadRequest
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import Response, HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.accounts.models import Account
from src.database.accounts.models import AccountType
from src.database.client import WalterDB
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class GetAccounts(WalterAPIMethod):
    """WalterAPI: GetAccounts"""

    API_NAME = "GetAccounts"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer"}
    REQUIRED_FIELDS = []
    EXCEPTIONS = [
        BadRequest,
        NotAuthenticated,
        UserDoesNotExist,
    ]

    walter_db: WalterDB

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
    ) -> None:
        super().__init__(
            GetAccounts.API_NAME,
            GetAccounts.REQUIRED_QUERY_FIELDS,
            GetAccounts.REQUIRED_HEADERS,
            GetAccounts.REQUIRED_FIELDS,
            GetAccounts.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db

    def execute(self, event: dict, authenticated_email: str) -> Response:
        user = self._verify_user_exists(self.walter_db, authenticated_email)
        accounts = self.walter_db.get_accounts(user.user_id)
        accounts = self._update_account_balances(accounts)
        return Response(
            api_name=GetAccounts.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Successfully retrieved accounts!",
            data={
                "total_num_accounts": len(accounts),
                "total_balance": sum([account.balance for account in accounts]),
                "accounts": [account.to_dict() for account in accounts],
            },
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True

    def _update_account_balances(self, accounts: List[Account]) -> List[Account]:
        if len(accounts) == 0:
            log.info("No accounts found to update balances for!")
            return []

        log.info("Updating account balances...")

        update_account_balance_cutoff = datetime.now(timezone.utc) - timedelta(
            minutes=10
        )

        updated_accounts = []
        for account in accounts:
            if (
                account.account_type == AccountType.INVESTMENT
                and account.balance_last_updated_at < update_account_balance_cutoff
            ):
                log.info(f"Updating balance for account '{account.account_id}'")
                holdings = self.walter_db.get_holdings(account.account_id)

                holdings_securities = []
                holdings_quantities = {}
                for holding in holdings:
                    holdings_securities.append(holding.security_id)
                    holdings_quantities[holding.security_id] = holding.quantity

                investment_account_balance = 0
                for security in holdings_securities:
                    price = self.walter_db.get_security(security).current_price
                    security_equity = price * holdings_quantities[security]
                    investment_account_balance += security_equity
                    log.info(
                        f"Investment account balance for security '{security}': {security_equity}"
                    )

                account.balance = investment_account_balance
                account.balance_last_updated_at = datetime.now(timezone.utc)
                self.walter_db.update_account(account)
                log.info(f"Updated balance for account '{account.account_id}'")

            updated_accounts.append(account)

        return updated_accounts
