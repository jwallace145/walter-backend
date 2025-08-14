import json
from dataclasses import dataclass

from src.api.common.exceptions import (
    NotAuthenticated,
    UserDoesNotExist,
    AccountDoesNotExist,
    BadRequest,
)
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import Response, Status, HTTPStatus
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.database.users.models import User
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class DeleteAccount(WalterAPIMethod):
    """WalterAPI: DeleteAccount"""

    API_NAME = "DeleteAccount"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer", "content-type": "application/json"}
    REQUIRED_FIELDS = ["account_id"]
    EXCEPTIONS = [
        BadRequest,
        NotAuthenticated,
        UserDoesNotExist,
        AccountDoesNotExist,
    ]

    walter_db: WalterDB

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
    ) -> None:
        super().__init__(
            DeleteAccount.API_NAME,
            DeleteAccount.REQUIRED_QUERY_FIELDS,
            DeleteAccount.REQUIRED_HEADERS,
            DeleteAccount.REQUIRED_FIELDS,
            DeleteAccount.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db

    def execute(self, event: dict, authenticated_email: str) -> Response:
        user = self._verify_user_exists(self.walter_db, authenticated_email)
        self._verify_account_exists(user, event)
        self._delete_account(user, event)
        return Response(
            api_name=DeleteAccount.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Successfully deleted account!",
        )

    def validate_fields(self, event: dict) -> None:
        # Base class validates REQUIRED_FIELDS; nothing additional here.
        pass

    def is_authenticated_api(self) -> bool:
        return True

    def _verify_account_exists(self, user: User, event: dict) -> None:
        """
        Verifies whether an account exists for the user.

        Args:
            user: The authenticated `User` object.
            event: The request event containing account data.

        Raises:
            AccountDoesNotExist: If the account doesn't exist.
        """
        log.info("Verifying account exists for user")

        body = json.loads(event["body"])
        account_id = body["account_id"]

        account = self.walter_db.get_account(
            user_id=user.user_id,
            account_id=account_id,
        )

        if not account:
            raise AccountDoesNotExist("Account does not exist!")

        log.info("Account verified successfully!")

    def _delete_account(self, user: User, event: dict) -> None:
        """
        Deletes an account for the user, including its transactions.

        Args:
            user: The authenticated `User` object.
            event: The request event containing account data.

        Returns:
            None
        """
        log.info("Deleting account for user")

        # get account id from request body
        body = json.loads(event["body"])
        account_id = body["account_id"]

        log.info(f"Deleting transactions for account '{account_id}'")
        self.walter_db.delete_account_transactions(account_id)

        log.info(f"Deleting holdings for account '{account_id}'")
        self.walter_db.delete_account_holdings(account_id)

        log.info(f"Deleting account '{account_id}'")
        self.walter_db.delete_account(user.user_id, account_id)

        log.info("Account deleted successfully!")
