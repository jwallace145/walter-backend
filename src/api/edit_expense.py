import datetime as dt
import json
from dataclasses import dataclass

from src.api.common.exceptions import (
    BadRequest,
    NotAuthenticated,
    UserDoesNotExist,
)
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import Response, HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.database.expenses.models import Expense, ExpenseCategory
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class EditExpense(WalterAPIMethod):
    """
    WalterAPI: EditExpense

    This API edits an existing user expense and updates
    the database accordingly.
    """

    API_NAME = "EditExpense"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer", "content-type": "application/json"}
    REQUIRED_FIELDS = ["date", "expense_id", "vendor", "amount", "category"]
    EXCEPTIONS = [BadRequest, NotAuthenticated, UserDoesNotExist]

    walter_db: WalterDB

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
    ) -> None:
        super().__init__(
            EditExpense.API_NAME,
            EditExpense.REQUIRED_QUERY_FIELDS,
            EditExpense.REQUIRED_HEADERS,
            EditExpense.REQUIRED_FIELDS,
            EditExpense.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db

    def execute(self, event: dict, authenticated_email: str) -> Response:
        expense = self._get_expense(event, authenticated_email)
        self.walter_db.put_expense(expense)
        return Response(
            api_name=EditExpense.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Expense edited!",
            data={
                "expense": expense.to_dict(),
            },
        )

    def _get_expense(self, event: dict, authenticated_email: str) -> Expense:
        body = json.loads(event["body"])
        date = EditExpense._get_date(body["date"])
        expense_id = body["expense_id"]
        vendor = body["vendor"]
        amount = EditExpense._get_expense_amount(body["amount"])
        category = EditExpense._get_expense_category(body["category"])
        return Expense(
            user_email=authenticated_email,
            date=date,
            vendor=vendor,
            amount=amount,
            category=category,
            expense_id=expense_id,
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True

    @staticmethod
    def _get_date(date: str) -> dt.datetime:
        try:
            return dt.datetime.strptime(date, "%Y-%m-%d")
        except Exception:
            log.error(f"Invalid date: {date}")
            raise BadRequest(f"Invalid date '{date}'!")

    @staticmethod
    def _get_expense_amount(amount: str) -> float:
        try:
            return float(amount)
        except Exception:
            log.error(f"Invalid expense amount: {amount}")
            raise BadRequest(f"Invalid expense amount '{amount}'!")

    @staticmethod
    def _get_expense_category(category: str) -> ExpenseCategory:
        try:
            return ExpenseCategory.from_string(category)
        except Exception:
            log.error(f"Invalid expense category: {category}")
            raise BadRequest(f"Invalid expense category '{category}'!")
