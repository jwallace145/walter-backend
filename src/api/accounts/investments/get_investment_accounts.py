from dataclasses import dataclass

from src.api.common.exceptions import NotAuthenticated, UserDoesNotExist
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import Response, HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class GetInvestmentAccounts(WalterAPIMethod):
    """WalterAPI: GetInvestmentAccounts"""

    API_NAME = "GetInvestmentAccounts"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer"}
    REQUIRED_FIELDS = []
    EXCEPTIONS = [
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
            GetInvestmentAccounts.API_NAME,
            GetInvestmentAccounts.REQUIRED_QUERY_FIELDS,
            GetInvestmentAccounts.REQUIRED_HEADERS,
            GetInvestmentAccounts.REQUIRED_FIELDS,
            GetInvestmentAccounts.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db

    def execute(self, event: dict, authenticated_email: str) -> Response:
        user = self._verify_user_exists(self.walter_db, authenticated_email)
        investment_accounts = self.walter_db.get_investment_accounts(user.user_id)
        log.info(f"Retrieved {len(investment_accounts)} investment accounts for user")
        return Response(
            api_name=GetInvestmentAccounts.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Successfully retrieved investment accounts!",
            data={
                "total_num_investment_accounts": len(investment_accounts),
                "total_investment_balance": sum(
                    [account.balance for account in investment_accounts]
                ),
                "investment_accounts": [
                    account.to_dict() for account in investment_accounts
                ],
            },
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True
