import json
from dataclasses import dataclass

from src.api.common.exceptions import BadRequest, NotAuthenticated, UserDoesNotExist
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import Response, HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.utils.log import Logger
import datetime as dt

log = Logger(__name__).get_logger()


@dataclass
class DeleteExpense(WalterAPIMethod):
    """
    WalterAPI: DeleteExpense

    This API deletes a user expense from the Expenses table
    in WalterDB.
    """

    API_NAME = "DeleteExpense"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer", "content-type": "application/json"}
    REQUIRED_FIELDS = ["date", "expense_id"]
    EXCEPTIONS = [BadRequest, NotAuthenticated, UserDoesNotExist]

    walter_db: WalterDB

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
    ) -> None:
        super().__init__(
            DeleteExpense.API_NAME,
            DeleteExpense.REQUIRED_QUERY_FIELDS,
            DeleteExpense.REQUIRED_HEADERS,
            DeleteExpense.REQUIRED_FIELDS,
            DeleteExpense.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db

    def execute(self, event: dict, authenticated_email: str) -> Response:
        body = json.loads(event["body"])
        date = dt.datetime.strptime(body["date"], "%Y-%m-%d")
        expense_id = body["expense_id"]
        self.walter_db.delete_expense(authenticated_email, date, expense_id)
        return Response(
            api_name=DeleteExpense.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Expense deleted!",
            data={
                "expense": {
                    "user_email": authenticated_email,
                    "date": date.strftime("%Y-%m-%d"),
                    "expense_id": expense_id,
                }
            },
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True
