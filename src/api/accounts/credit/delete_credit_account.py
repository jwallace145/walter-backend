import json
from dataclasses import dataclass
from src.api.common.exceptions import (
    NotAuthenticated,
    UserDoesNotExist,
    CreditAccountDoesNotExist,
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
class DeleteCreditAccount(WalterAPIMethod):
    """WalterAPI: DeleteCreditAccount"""

    API_NAME = "DeleteCreditAccount"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer", "content-type": "application/json"}
    REQUIRED_FIELDS = ["account_id"]
    EXCEPTIONS = [
        NotAuthenticated,
        UserDoesNotExist,
        CreditAccountDoesNotExist,
    ]

    walter_db: WalterDB

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
    ) -> None:
        super().__init__(
            DeleteCreditAccount.API_NAME,
            DeleteCreditAccount.REQUIRED_QUERY_FIELDS,
            DeleteCreditAccount.REQUIRED_HEADERS,
            DeleteCreditAccount.REQUIRED_FIELDS,
            DeleteCreditAccount.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db

    def execute(self, event: dict, authenticated_email: str) -> Response:
        user = self._verify_user_exists(self.walter_db, authenticated_email)
        self._verify_credit_account_exists(user, event)
        self._delete_credit_account(user, event)
        return Response(
            api_name=DeleteCreditAccount.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Successfully deleted credit account!",
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True

    def _verify_credit_account_exists(self, user: User, event: dict) -> None:
        """
        Verifies whether a credit account exists for the user.

        Args:
            user: The authenticated `User` object.
            event: The request event containing credit account data.

        Raises:
            CreditAccountDoesNotExist: If the account doesn't exist.
        """
        log.info("Verifying credit account exists for user")

        body = json.loads(event["body"])
        account_id = body["account_id"]

        credit_account = self.walter_db.get_credit_account(
            user_id=user.user_id,
            account_id=account_id,
        )

        if not credit_account:
            raise CreditAccountDoesNotExist("Credit account does not exist!")

        log.info("Credit account verified successfully!")

    def _delete_credit_account(self, user: User, event: dict) -> None:
        """
        Deletes a credit account for the user.

        Args:
            user: The authenticated `User` object.
            event: The request event containing credit account data.

        Returns:
            None
        """
        log.info("Deleting credit account for user")

        # get account id from request body
        body = json.loads(event["body"])
        account_id = body["account_id"]

        # delete credit account and transactions from db
        self.walter_db.delete_transactions(user_id=user.user_id, account_id=account_id)
        self.walter_db.delete_credit_account(
            user_id=user.user_id, account_id=account_id
        )

        log.info("Credit account deleted successfully!")
