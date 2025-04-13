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
class GetExpenses(WalterAPIMethod):
    """
    WalterAPI: GetExpenses

    This API gets the expenses for a user from the Expenses
    table in WalterDB.
    """

    API_NAME = "GetExpenses"
    REQUIRED_QUERY_FIELDS = ["start_date", "end_date"]
    REQUIRED_HEADERS = {"Authorization": "Bearer"}
    REQUIRED_FIELDS = []
    EXCEPTIONS = [
        BadRequest,
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
            GetExpenses.API_NAME,
            GetExpenses.REQUIRED_QUERY_FIELDS,
            GetExpenses.REQUIRED_HEADERS,
            GetExpenses.REQUIRED_FIELDS,
            GetExpenses.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db

    def execute(self, event: dict, authenticated_email: str) -> Response:
        start_date = dt.datetime.strptime(
            WalterAPIMethod.get_query_field(event, "start_date"), "%Y-%m-%d"
        )
        end_date = dt.datetime.strptime(
            WalterAPIMethod.get_query_field(event, "end_date"), "%Y-%m-%d"
        )
        expenses = self.walter_db.get_expenses(
            authenticated_email, start_date, end_date
        )
        return Response(
            api_name=GetExpenses.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Retrieved expenses!",
            data={
                "expenses": [expense.to_dict() for expense in expenses],
            },
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True
