import datetime as dt
import json
from dataclasses import dataclass

from src.api.common.exceptions import (BadRequest, NotAuthenticated,
                                       UserDoesNotExist)
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Response, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.database.users.models import User
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class DeleteTransaction(WalterAPIMethod):
    """
    WalterAPI: DeleteTransaction

    This API deletes a user transaction from the Transactions table
    in WalterDB.
    """

    API_NAME = "DeleteTransaction"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer", "content-type": "application/json"}
    REQUIRED_FIELDS = ["date", "transaction_id"]
    EXCEPTIONS = [BadRequest, NotAuthenticated, UserDoesNotExist]

    walter_db: WalterDB

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
    ) -> None:
        super().__init__(
            DeleteTransaction.API_NAME,
            DeleteTransaction.REQUIRED_QUERY_FIELDS,
            DeleteTransaction.REQUIRED_HEADERS,
            DeleteTransaction.REQUIRED_FIELDS,
            DeleteTransaction.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db

    def execute(self, event: dict, authenticated_email: str) -> Response:
        user = self._verify_user_exists(authenticated_email)
        body = json.loads(event["body"])
        date = dt.datetime.strptime(body["date"], "%Y-%m-%d")
        transaction_id = body["transaction_id"]
        self.walter_db.delete_transaction(user.user_id, date, transaction_id)
        return Response(
            api_name=DeleteTransaction.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Expense deleted!",
            data={
                "expense": {
                    "user_email": authenticated_email,
                    "date": date.strftime("%Y-%m-%d"),
                    "expense_id": transaction_id,
                }
            },
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True

    def _verify_user_exists(self, email: str) -> User:
        log.info(f"Verifying user exists with email '{email}'")
        user = self.walter_db.get_user_by_email(email)
        if user is None:
            raise UserDoesNotExist(f"User with email '{email}' does not exist!")
        log.info("Verified user exists!")
        return user
