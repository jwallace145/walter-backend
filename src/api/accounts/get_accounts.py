from dataclasses import dataclass

from src.api.common.exceptions import NotAuthenticated, UserDoesNotExist, BadRequest
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import Response, HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
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
