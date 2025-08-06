import json
from dataclasses import dataclass

from src.api.common.exceptions import (
    NotAuthenticated,
    UserDoesNotExist,
    CashAccountDoesNotExist,
)
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import Response, Status, HTTPStatus
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.accounts.cash.models import CashAccount
from src.database.client import WalterDB
from src.database.users.models import User
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class DeleteCashAccount(WalterAPIMethod):
    """
    WalterAPI: DeleteCashAccount
    """

    API_NAME = "DeleteCashAccount"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer", "content-type": "application/json"}
    REQUIRED_FIELDS = ["account_id"]
    EXCEPTIONS = [NotAuthenticated, UserDoesNotExist, CashAccountDoesNotExist]

    walter_db: WalterDB

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
    ) -> None:
        super().__init__(
            DeleteCashAccount.API_NAME,
            DeleteCashAccount.REQUIRED_QUERY_FIELDS,
            DeleteCashAccount.REQUIRED_HEADERS,
            DeleteCashAccount.REQUIRED_FIELDS,
            DeleteCashAccount.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db

    def execute(self, event: dict, authenticated_email: str) -> Response:
        user = self._verify_user_exists(self.walter_db, authenticated_email)
        self._verify_cash_account_exists(user, event)
        self._delete_cash_account(user, event)
        return Response(
            api_name=DeleteCashAccount.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Cash account deleted successfully!",
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True

    def _verify_cash_account_exists(self, user: User, event: dict) -> CashAccount:
        log.info("Verifying cash account exists for user")

        body = json.loads(event["body"])
        account_id = body["account_id"]
        cash_account = self.walter_db.get_cash_account(
            user_id=user.user_id,
            account_id=account_id,
        )

        if not cash_account:
            raise CashAccountDoesNotExist(
                f"Cash account with ID '{account_id}' does not exist!"
            )

        log.info("Cash account verified successfully!")
        return cash_account

    def _delete_cash_account(self, user: User, event: dict) -> None:
        """
        Deletes a cash account for the user.

        Args:
            user: The authenticated `User` object.
            event: The request event containing cash account data.

        Returns:
            None
        """
        log.info("Deleting cash account for user")

        # get account id from request body
        body = json.loads(event["body"])
        account_id = body["account_id"]

        # delete cash account and transactions from db
        self.walter_db.delete_transactions(user_id=user.user_id, account_id=account_id)
        self.walter_db.delete_cash_account(user_id=user.user_id, account_id=account_id)

        log.info("Cash account deleted successfully!")
