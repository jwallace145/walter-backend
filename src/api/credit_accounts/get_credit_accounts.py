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
class GetCreditAccounts(WalterAPIMethod):
    """WalterAPI: GetCreditAccounts"""

    API_NAME = "GetCreditAccounts"
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
            GetCreditAccounts.API_NAME,
            GetCreditAccounts.REQUIRED_QUERY_FIELDS,
            GetCreditAccounts.REQUIRED_HEADERS,
            GetCreditAccounts.REQUIRED_FIELDS,
            GetCreditAccounts.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db

    def execute(self, event: dict, authenticated_email: str) -> Response:
        user = self._verify_user_exists(self.walter_db, authenticated_email)
        credit_accounts = self.walter_db.get_credit_accounts(user.user_id)
        log.info(f"Retrieved {len(credit_accounts)} credit accounts for user")
        return Response(
            api_name=GetCreditAccounts.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Successfully retrieved credit accounts!",
            data={
                "total_num_credit_accounts": len(credit_accounts),
                "total_credit_balance": sum(
                    [account.balance for account in credit_accounts]
                ),
                "credit_accounts": [account.to_dict() for account in credit_accounts],
            },
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True
