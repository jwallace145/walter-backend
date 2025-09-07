from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from src.api.accounts.get_accounts.models import GetAccountsResponseData
from src.api.common.exceptions import (
    BadRequest,
    NotAuthenticated,
    SessionDoesNotExist,
    UserDoesNotExist,
)
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Response, Status
from src.auth.authenticator import WalterAuthenticator
from src.database.accounts.models import Account, AccountType, InvestmentAccount
from src.database.client import WalterDB
from src.database.holdings.models import Holding
from src.database.securities.models import Security
from src.database.sessions.models import Session
from src.database.users.models import User
from src.environment import Domain
from src.metrics.client import DatadogMetricsClient
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
        (BadRequest, HTTPStatus.BAD_REQUEST),
        (NotAuthenticated, HTTPStatus.UNAUTHORIZED),
        (SessionDoesNotExist, HTTPStatus.NOT_FOUND),
        (UserDoesNotExist, HTTPStatus.NOT_FOUND),
    ]

    def __init__(
        self,
        domain: Domain,
        walter_authenticator: WalterAuthenticator,
        metrics: DatadogMetricsClient,
        walter_db: WalterDB,
    ) -> None:
        super().__init__(
            domain,
            GetAccounts.API_NAME,
            GetAccounts.REQUIRED_QUERY_FIELDS,
            GetAccounts.REQUIRED_HEADERS,
            GetAccounts.REQUIRED_FIELDS,
            GetAccounts.EXCEPTIONS,
            walter_authenticator,
            metrics,
            walter_db,
        )

    def execute(self, event: dict, session: Optional[Session]) -> Response:
        user: User = self._verify_user_exists(session.user_id)
        accounts: List[Account] = self._get_user_accounts(user)
        holdings: List[Holding] = self._get_user_holdings(user, accounts)
        securities: List[Security] = self._get_user_securities(user, holdings)
        # TODO: Move logic from model class to this class so model class is not as complex
        data: GetAccountsResponseData = GetAccountsResponseData.create(
            user, accounts, holdings, securities
        )
        self._update_investment_account_balances(user, data, accounts)
        return Response(
            domain=self.domain,
            api_name=GetAccounts.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Successfully retrieved accounts!",
            data=data.to_dict(),
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True

    def _get_user_accounts(self, user: User) -> List[Account]:
        log.info(f"Getting all accounts for user: {user.user_id}")
        accounts: List[Account] = self.db.get_accounts(user.user_id)
        log.info(f"Found {len(accounts)} account(s) for user!")
        return accounts

    def _get_user_holdings(self, user: User, accounts: List[Account]) -> List[Holding]:
        log.info(f"Getting holdings for user: {user.user_id}")
        holdings: List[Holding] = []
        for account in accounts:
            if account.account_type == AccountType.INVESTMENT and isinstance(
                account, InvestmentAccount
            ):
                holdings.extend(self.db.get_holdings(account.account_id))
        log.info(f"Found {len(holdings)} holding(s) for user!")
        return holdings

    def _get_user_securities(
        self, user: User, holdings: List[Holding]
    ) -> List[Security]:
        log.info(f"Getting securities for user: {user.user_id}")
        security_ids: List[str] = [holding.security_id for holding in holdings]
        securities: List[Security] = []
        for security_id in security_ids:
            security: Security = self.db.get_security(security_id)
            securities.append(security)
        log.info(
            f"Found {len(securities)} security(s) for user across all investment accounts!"
        )
        return securities

    def _update_investment_account_balances(
        self,
        user: User,
        data: GetAccountsResponseData,
        accounts: List[Account],
    ) -> None:
        # create account ids to account balance map
        account_id_to_balance: dict[str, float] = {}
        for account in data.to_dict()["accounts"]:
            account_id_to_balance[account["account_id"]] = account["balance"]

        # update investment account balances
        log.info(f"Updating investment account balances for user: {user.user_id}")
        for account in accounts:
            if account.account_type == AccountType.INVESTMENT and isinstance(
                account, InvestmentAccount
            ):
                now = datetime.now(timezone.utc)
                account.balance = account_id_to_balance[account.account_id]
                account.balance_last_updated_at = now
                account.updated_at = now
                self.db.update_account(account)
