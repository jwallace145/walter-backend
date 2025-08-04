import json
from dataclasses import dataclass

from src.api.common.exceptions import NotAuthenticated, UserDoesNotExist
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import Response, Status, HTTPStatus
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.cash_accounts.models import CashAccount, CashAccountType
from src.database.client import WalterDB
from src.database.users.models import User
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class CreateCashAccount(WalterAPIMethod):
    """
    WalterAPI: CreateCashAccount
    """

    API_NAME = "CreateCashAccount"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer"}
    REQUIRED_FIELDS = [
        "bank_name",
        "account_name",
        "balance",
        "account_last_four_numbers",
    ]
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
            CreateCashAccount.API_NAME,
            CreateCashAccount.REQUIRED_QUERY_FIELDS,
            CreateCashAccount.REQUIRED_HEADERS,
            CreateCashAccount.REQUIRED_FIELDS,
            CreateCashAccount.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db

    def execute(self, event: dict, authenticated_email: str) -> Response:
        user = self._verify_user_exists(authenticated_email)
        cash_account = self._create_new_cash_account(user, event)
        return Response(
            api_name=CreateCashAccount.API_NAME,
            http_status=HTTPStatus.CREATED,
            status=Status.SUCCESS,
            message="Cash account created successfully!",
            data={"cash_account": cash_account.to_dict()},
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
        log.info(f"Verifying user existence for email: {email}")
        user = self.walter_db.get_user_by_email(email)
        if user is None:
            raise UserDoesNotExist(f"User with email '{email}' does not exist!")
        log.info("User verified successfully!")
        return user

    def _create_new_cash_account(self, user: User, event: dict) -> CashAccount:
        log.info("Creating new cash account for user")

        body = json.loads(event["body"])
        cash_account = CashAccount.create_new_account(
            user,
            bank_name=body["bank_name"],
            account_name=body["account_name"],
            account_type=CashAccountType.CHECKING,
            account_last_four_numbers=body["account_last_four_numbers"],
            balance=float(body["balance"]),
        )

        cash_account = self.walter_db.create_cash_account(cash_account)
        log.info("Cash account created for user successfully!")

        return cash_account
