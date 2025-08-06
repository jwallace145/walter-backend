import datetime as dt
import json
from dataclasses import dataclass

from src.api.common.exceptions import (
    NotAuthenticated,
    UserDoesNotExist,
    CashAccountDoesNotExist,
    BadRequest,
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
class UpdateCashAccount(WalterAPIMethod):
    """
    WalterAPI: UpdateCashAccount
    """

    API_NAME = "UpdateCashAccount"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer", "content-type": "application/json"}
    REQUIRED_FIELDS = [
        "account_id",
        "bank_name",
        "account_name",
        "account_last_four_numbers",
        "balance",
    ]
    EXCEPTIONS = [
        NotAuthenticated,
        UserDoesNotExist,
        CashAccountDoesNotExist,
    ]

    walter_db: WalterDB

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
    ) -> None:
        super().__init__(
            UpdateCashAccount.API_NAME,
            UpdateCashAccount.REQUIRED_QUERY_FIELDS,
            UpdateCashAccount.REQUIRED_HEADERS,
            UpdateCashAccount.REQUIRED_FIELDS,
            UpdateCashAccount.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db

    def execute(self, event: dict, authenticated_email: str) -> Response:
        user = self._verify_user_exists(authenticated_email)
        account = self._verify_cash_account_exists(user, event)
        self._update_cash_account(account, event)
        return Response(
            api_name=UpdateCashAccount.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Cash account updated successfully!",
            data={"account": account.to_dict()},
        )

    def validate_fields(self, event: dict) -> None:
        body = json.loads(event["body"])
        account_last_four_numbers = body["account_last_four_numbers"]
        if len(account_last_four_numbers) != 4:
            raise BadRequest("Account last four numbers must be four digits long!")

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
        log.info(f"Verifying user existence for email: {email}")
        user = self.walter_db.get_user_by_email(email)
        if user is None:
            raise UserDoesNotExist(f"User with email '{email}' does not exist!")
        log.info("User verified successfully!")
        return user

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

    def _update_cash_account(self, account: CashAccount, event: dict) -> None:
        """
        Updates an existing cash account for the user.

        Args:
            user: The `User` object of the authenticated user.
            event: The request event containing updated cash account data.

        Returns:
            None
        """
        log.info("Updating cash account for user")

        # get request body fields
        body = json.loads(event["body"])
        bank_name = body["bank_name"]
        account_name = body["account_name"]
        balance = float(body["balance"])
        account_last_four_numbers = body["account_last_four_numbers"]

        # update cash account fields
        account.bank_name = bank_name
        account.account_name = account_name
        account.account_last_four_numbers = account_last_four_numbers
        account.balance = balance
        account.updated_at = dt.datetime.now(dt.UTC)

        self.walter_db.update_cash_account(account)

        log.info("Cash account updated successfully!")
