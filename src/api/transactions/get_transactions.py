from dataclasses import dataclass

from src.api.common.exceptions import BadRequest, NotAuthenticated, UserDoesNotExist
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import Response, HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.database.users.models import User
from src.utils.log import Logger
import datetime as dt
from typing import Tuple

log = Logger(__name__).get_logger()


@dataclass
class GetTransactions(WalterAPIMethod):
    """
    WalterAPI: GetTransactions

    This API gets the transactions for the user over a given
    period of time from the Transactions table in WalterDB.
    """

    API_NAME = "GetTransactions"
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
            GetTransactions.API_NAME,
            GetTransactions.REQUIRED_QUERY_FIELDS,
            GetTransactions.REQUIRED_HEADERS,
            GetTransactions.REQUIRED_FIELDS,
            GetTransactions.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db

    def execute(self, event: dict, authenticated_email: str) -> Response:
        user = self._verify_user_exists(authenticated_email)
        start_date, end_date = self._get_date_range(event)
        transactions = self.walter_db.get_transactions(
            user.user_id, start_date, end_date
        )
        unreviewed_transactions = [
            transaction
            for transaction in transactions
            if not transaction.transaction.is_reviewed()
        ]
        income_transactions = [
            transaction
            for transaction in transactions
            if transaction.transaction.is_income()
        ]
        total_income = sum(
            [transaction.transaction.amount for transaction in income_transactions]
        )
        expense_transactions = [
            transaction
            for transaction in transactions
            if transaction.transaction.is_expense()
        ]
        total_expenses = sum(
            [transaction.transaction.amount for transaction in expense_transactions]
        )
        return Response(
            api_name=GetTransactions.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Retrieved transactions!",
            data={
                "num_transactions": len(transactions),
                "num_unreviewed_transactions": len(unreviewed_transactions),
                "total_income": total_income,
                "total_expense": total_expenses,
                "cash_flow": total_income - total_expenses,
                "transactions": [transaction.to_dict() for transaction in transactions],
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

    def _get_date_range(self, event: dict) -> Tuple[dt.datetime, dt.datetime]:
        start_date = dt.datetime.strptime(
            WalterAPIMethod.get_query_field(event, "start_date"), "%Y-%m-%d"
        )
        end_date = dt.datetime.strptime(
            WalterAPIMethod.get_query_field(event, "end_date"), "%Y-%m-%d"
        )
        return [start_date, end_date]
