from dataclasses import dataclass

from src.api.common.exceptions import NotAuthenticated, UserDoesNotExist
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import Response, HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.database.users.models import User
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class GetCashAccounts(WalterAPIMethod):
    """
    WalterAPI: GetCashAccounts
    """

    API_NAME = "GetCashAccounts"
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
            GetCashAccounts.API_NAME,
            GetCashAccounts.REQUIRED_QUERY_FIELDS,
            GetCashAccounts.REQUIRED_HEADERS,
            GetCashAccounts.REQUIRED_FIELDS,
            GetCashAccounts.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db

    def execute(self, event: dict, authenticated_email: str) -> Response:
        user = self._verify_user_exists(authenticated_email)
        cash_accounts = self.walter_db.get_cash_accounts(user.user_id)
        log.info(f"Retrieved {len(cash_accounts)} cash accounts for user")
        return Response(
            api_name=GetCashAccounts.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Retrieved cash accounts successfully!",
            data={
                "total_num_cash_accounts": len(cash_accounts),
                "total_cash": sum([account.balance for account in cash_accounts]),
                "cash_accounts": [account.to_dict() for account in cash_accounts],
            },
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True

    def _verify_user_exists(self, email: str) -> User:
        """
        Verifies whether a user exists based on the provided email.

        Args:
            email: The email of the user.

        Returns:
            The `User` object if the user exists.

        Raises:
            UserDoesNotExist: If the user doesn't exist.
        """
        log.info(f"Verifying user exists with email '{email}'")
        user = self.walter_db.get_user_by_email(email)
        if user is None:
            raise UserDoesNotExist(f"User with email '{email}' does not exist!")
        log.info("Verified user exists!")
        return user
