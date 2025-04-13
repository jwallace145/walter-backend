import json
from dataclasses import dataclass

from src.api.common.exceptions import (
    BadRequest,
    NotAuthenticated,
    UserDoesNotExist,
    InvalidExpenseCategory,
)
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import Response, HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.database.expenses.models import Expense, ExpenseCategory
from src.utils.log import Logger
import datetime as dt

log = Logger(__name__).get_logger()


@dataclass
class AddExpense(WalterAPIMethod):
    """
    WalterAPI: AddExpense

    This API adds an expense for the user to the Expenses
    table in WalterDB.
    """

    API_NAME = "AddExpense"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer", "content-type": "application/json"}
    REQUIRED_FIELDS = [
        "date",
        "vendor",
        "amount",
        "category",
    ]
    EXCEPTIONS = [
        BadRequest,
        NotAuthenticated,
        UserDoesNotExist,
        InvalidExpenseCategory,
    ]

    walter_db: WalterDB

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
    ) -> None:
        super().__init__(
            AddExpense.API_NAME,
            AddExpense.REQUIRED_QUERY_FIELDS,
            AddExpense.REQUIRED_HEADERS,
            AddExpense.REQUIRED_FIELDS,
            AddExpense.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db

    def execute(self, event: dict, authenticated_email: str) -> Response:
        expense = self._get_expense(event, authenticated_email)
        self.walter_db.add_expense(expense)
        return Response(
            api_name=AddExpense.API_NAME,
            http_status=HTTPStatus.CREATED,
            status=Status.SUCCESS,
            message="Expense added!",
            data={
                "expense": expense.to_dict(),
            },
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True

    def _get_expense(self, event: dict, authenticated_email: str) -> Expense:
        body = json.loads(event["body"])

        # get category from enum of expense categories
        # if invalid category detected, throw invalid expense category exception
        category = None
        try:
            category_str = body["category"]
            category = ExpenseCategory.from_string(category_str)
        except Exception:
            log.error(
                f"Invalid expense category '{category_str}'! Valid expense categories: {[category.value for category in ExpenseCategory]}"
            )
            raise InvalidExpenseCategory(f"Invalid expense category '{category_str}'!")

        return Expense(
            user_email=authenticated_email,
            date=dt.datetime.strptime(body["date"], "%Y-%m-%d"),
            vendor=body["vendor"],
            amount=body["amount"],
            category=category,
        )
