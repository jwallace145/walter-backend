import json
from dataclasses import dataclass
from datetime import datetime, timezone
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
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.accounts.models import Account, AccountType
from src.database.client import WalterDB
from src.database.sessions.models import Session
from src.database.users.models import User
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class UpdateAccount(WalterAPIMethod):
    """WalterAPI: UpdateAccount"""

    API_NAME = "UpdateAccount"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer", "content-type": "application/json"}
    REQUIRED_FIELDS = [
        "account_id",
        "account_type",
        "account_subtype",
        "institution_name",
        "account_name",
        "account_mask",
        "balance",
        "logo_url",
    ]
    EXCEPTIONS = [
        BadRequest,
        NotAuthenticated,
        UserDoesNotExist,
        AccountDoesNotExist,
    ]

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
    ) -> None:
        super().__init__(
            UpdateAccount.API_NAME,
            UpdateAccount.REQUIRED_QUERY_FIELDS,
            UpdateAccount.REQUIRED_HEADERS,
            UpdateAccount.REQUIRED_FIELDS,
            UpdateAccount.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
            walter_db,
        )

    def execute(self, event: dict, session: Optional[Session]) -> Response:
        user = self._verify_user_exists(session.user_id)
        account = self._verify_account_exists(user, event)
        updated_account = self._update_account(user, account, event)
        return Response(
            api_name=UpdateAccount.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Account updated successfully!",
            data={"account": updated_account.to_dict()},
        )

    def validate_fields(self, event: dict) -> None:
        body = json.loads(event["body"])

        # Validate balance can be parsed as float
        try:
            float(body.get("balance"))
        except Exception:
            raise BadRequest("Invalid balance! Must be a number.")

        # Validate account_type is recognized
        try:
            AccountType.from_string(body.get("account_type", ""))
        except Exception:
            raise BadRequest(f"Invalid account type '{body.get('account_type')}'!")

    def is_authenticated_api(self) -> bool:
        return True

    def _verify_account_exists(self, user: User, event: dict) -> Account:
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

        return account

    def _update_account(self, user: User, account: Account, event: dict):
        log.info("Updating account for user")

        body = json.loads(event["body"])

        # Apply updates to mutable fields
        account.account_type = AccountType.from_string(body["account_type"])  # Enum
        account.account_subtype = body["account_subtype"]
        account.institution_name = body["institution_name"]
        account.account_name = body["account_name"]
        account.account_mask = body["account_mask"]
        account.balance = float(body["balance"])  # ensure float
        account.logo_url = body["logo_url"]
        account.updated_at = datetime.now(timezone.utc)

        # Persist changes
        updated = self.db.update_account(account)

        log.info("Account updated successfully!")
        return updated
