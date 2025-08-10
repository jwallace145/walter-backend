import json
from dataclasses import dataclass
from src.api.common.exceptions import (
    NotAuthenticated,
    UserDoesNotExist,
    InvestmentAccountDoesNotExist,
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
class DeleteInvestmentAccount(WalterAPIMethod):
    """WalterAPI: DeleteInvestmentAccount"""

    API_NAME = "DeleteInvestmentAccount"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer", "content-type": "application/json"}
    REQUIRED_FIELDS = ["account_id"]
    EXCEPTIONS = [
        NotAuthenticated,
        UserDoesNotExist,
        InvestmentAccountDoesNotExist,
    ]

    walter_db: WalterDB

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
    ) -> None:
        super().__init__(
            DeleteInvestmentAccount.API_NAME,
            DeleteInvestmentAccount.REQUIRED_QUERY_FIELDS,
            DeleteInvestmentAccount.REQUIRED_HEADERS,
            DeleteInvestmentAccount.REQUIRED_FIELDS,
            DeleteInvestmentAccount.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db

    def execute(self, event: dict, authenticated_email: str) -> Response:
        user = self._verify_user_exists(self.walter_db, authenticated_email)
        self._verify_investment_account_exists(user, event)
        self._delete_investment_account(user, event)
        return Response(
            api_name=DeleteInvestmentAccount.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Successfully deleted investment account!",
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True

    def _verify_investment_account_exists(self, user: User, event: dict) -> None:
        """
        Verifies whether an investment account exists for the user.

        Args:
            user: The authenticated `User` object.
            event: The request event containing investment account data.

        Raises:
            InvestmentAccountDoesNotExist: If the account doesn't exist.
        """
        log.info("Verifying investment account exists for user")

        body = json.loads(event["body"])
        account_id = body["account_id"]

        investment_account = self.walter_db.get_investment_account(
            user_id=user.user_id,
            account_id=account_id,
        )

        if not investment_account:
            raise InvestmentAccountDoesNotExist("Investment account does not exist!")

        log.info("Investment account verified successfully!")

    def _delete_investment_account(self, user: User, event: dict) -> None:
        """
        Deletes an investment account for the user.

        Args:
            user: The authenticated `User` object.
            event: The request event containing investment account data.

        Returns:
            None
        """
        log.info("Deleting investment account for user")

        # get account id from request body
        body = json.loads(event["body"])
        account_id = body["account_id"]

        # delete investment account and transactions from db
        self.walter_db.delete_transactions(user_id=user.user_id, account_id=account_id)
        self.walter_db.delete_investment_account(
            user_id=user.user_id, account_id=account_id
        )

        log.info("Investment account deleted successfully!")
