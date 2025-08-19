from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

from src.api.common.exceptions import BadRequest, NotAuthenticated, UserDoesNotExist
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Response, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.accounts.models import AccountType, InvestmentAccount
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
        accounts = self._get_accounts(user.user_id)
        return Response(
            api_name=GetAccounts.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Successfully retrieved accounts!",
            data={
                "total_num_accounts": len(accounts),
                "total_balance": sum([account["balance"] for account in accounts]),
                "accounts": accounts,
            },
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True

    def _get_accounts(self, user_id: str) -> List[dict]:
        log.info(f"Getting accounts for user '{user_id}'")
        accounts = self.walter_db.get_accounts(user_id)

        if len(accounts) == 0:
            log.info("No accounts found for user!")
            return []

        account_dicts = []
        for account in accounts:
            if account.account_type == AccountType.INVESTMENT and isinstance(
                account, InvestmentAccount
            ):
                log.info(
                    f"Updating balance for investment account '{account.account_id}'"
                )
                investment_account_dict = self._get_investment_account_dict(account)

                # update account balance
                account.balance = investment_account_dict["balance"]
                account.balance_last_updated_at = datetime.now(timezone.utc)
                self.walter_db.update_account(account)

                account_dicts.append(investment_account_dict)
            else:
                account_dicts.append(account.to_dict())

        return account_dicts

    def _get_investment_account_dict(
        self,
        account: InvestmentAccount,
    ) -> dict:
        # get current holdings for investment account
        holdings = self.walter_db.get_holdings(account.account_id)

        # get securities for holdings
        securities = []
        for holding in holdings:
            security = self.walter_db.get_security(holding.security_id)
            securities.append(security)

        # create securities dict for fast lookups
        securities_dict = {}
        for security in securities:
            securities_dict[security.security_id] = security

        account_holdings = []
        for holding in holdings:
            security = securities_dict[holding.security_id]
            account_holdings.append(
                {
                    "security_id": holding.security_id,
                    "security_name": security.security_name,
                    "quantity": holding.quantity,
                    "current_price": security.current_price,
                    "total_value": holding.quantity * security.current_price,
                    "average_cost_basis": holding.average_cost_basis,
                    "total_cost_basis": holding.total_cost_basis,
                    "gain_loss": holding.quantity * security.current_price
                    - holding.total_cost_basis,
                }
            )

        now = datetime.now(timezone.utc)
        return {
            "account_id": account.account_id,
            "account_name": account.account_name,
            "account_type": account.account_type.value,
            "balance": sum([holding["total_value"] for holding in account_holdings]),
            "total_gain_loss": sum(
                [holding["gain_loss"] for holding in account_holdings]
            ),
            "balance_last_updated_at": now.isoformat(),
            "holdings": account_holdings,
        }
