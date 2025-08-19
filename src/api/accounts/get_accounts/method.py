from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

from src.api.accounts.get_accounts.models import GetAccountsResponseData
from src.api.common.exceptions import BadRequest, NotAuthenticated, UserDoesNotExist
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Response, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.accounts.models import Account, AccountType, InvestmentAccount
from src.database.client import WalterDB
from src.database.holdings.models import Holding
from src.database.securities.models import Security
from src.database.users.models import User
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
        user: User = self._verify_user_exists(self.walter_db, authenticated_email)

        # get all accounts for user
        log.info(f"Getting all accounts for user: {user.user_id}")
        accounts: List[Account] = self.walter_db.get_accounts(user.user_id)

        # get holdings for investment accounts
        log.info(f"Getting holdings for user: {user.user_id}")
        holdings: List[Holding] = []
        for account in accounts:
            if account.account_type == AccountType.INVESTMENT and isinstance(
                account, InvestmentAccount
            ):
                holdings.extend(self.walter_db.get_holdings(account.account_id))

        # get securities included in user holdings across all accounts
        log.info(f"Getting securities for user: {user.user_id}")
        security_ids: List[str] = [holding.security_id for holding in holdings]
        securities: List[Security] = []
        for security_id in security_ids:
            security: Security = self.walter_db.get_security(security_id)
            securities.append(security)

        data: GetAccountsResponseData = GetAccountsResponseData.create(
            user, accounts, holdings, securities
        )

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
                self.walter_db.update_account(account)

        return Response(
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
