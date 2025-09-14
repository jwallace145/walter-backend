import json
from dataclasses import dataclass
from typing import Optional

from src.api.common.exceptions import (
    AccountDoesNotExist,
    BadRequest,
    NotAuthenticated,
    UserDoesNotExist,
)
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Response, Status
from src.auth.authenticator import WalterAuthenticator
from src.database.client import WalterDB
from src.database.sessions.models import Session
from src.database.users.models import User
from src.environment import Domain
from src.metrics.client import DatadogMetricsClient
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
        (BadRequest, HTTPStatus.BAD_REQUEST),
        (NotAuthenticated, HTTPStatus.UNAUTHORIZED),
        (UserDoesNotExist, HTTPStatus.NOT_FOUND),
        (AccountDoesNotExist, HTTPStatus.NOT_FOUND),
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
            DeleteAccount.API_NAME,
            DeleteAccount.REQUIRED_QUERY_FIELDS,
            DeleteAccount.REQUIRED_HEADERS,
            DeleteAccount.REQUIRED_FIELDS,
            DeleteAccount.EXCEPTIONS,
            walter_authenticator,
            metrics,
            walter_db,
        )

    def execute(self, event: dict, session: Optional[Session]) -> Response:
        user = self._verify_user_exists(session.user_id)
        self._verify_account_exists(user, event)
        self._delete_account(user, event)
        return self._create_response(
            HTTPStatus.OK,
            Status.SUCCESS,
            "Successfully deleted account!",
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

        account = self.db.get_account(
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
        self.db.delete_account_transactions(account_id)

        log.info(f"Deleting holdings for account '{account_id}'")
        self.db.delete_account_holdings(account_id)

        log.info(f"Deleting account '{account_id}'")
        self.db.delete_account(user.user_id, account_id)

        log.info("Account deleted successfully!")
