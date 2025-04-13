import json
from dataclasses import dataclass
from typing import List

from src.aws.dynamodb.client import WalterDDBClient
from src.database.expenses.models import Expense, ExpenseCategory
from src.environment import Domain
from src.utils.log import Logger
import datetime as dt

log = Logger(__name__).get_logger()


@dataclass
class ExpensesTable:

    EXPENSES_TABLE_NAME_FORMAT = "Expenses-{domain}"

    ddb: WalterDDBClient
    domain: Domain

    table: str = None  # set during post init

    def __post_init__(self) -> None:
        self.table = ExpensesTable._get_expenses_table_name(self.domain)
        log.debug(f"Creating ExpensesTable DDB client with table name '{self.table}'")

    def get_expenses(self, user_email: str) -> List[Expense]:
        log.info(f"Getting expenses for user '{user_email}' from table '{self.table}'")

        expense_items = self.ddb.query(
            table=self.table,
            query=ExpensesTable._get_expenses_by_user_query(user_email),
        )

        expenses = []
        for item in expense_items:
            expenses.append(ExpensesTable._get_expense_from_ddb_item(item))

        log.info(f"Returned {len(expenses)} expenses for user '{user_email}'")

        return expenses

    def put_expense(self, expense: Expense) -> None:
        log.info(f"Putting expense for user '{expense.user_email}' to Expenses table")
        log.debug(f"Expense:\n{json.dumps(expense.to_dict(), indent=4)}")
        self.ddb.put_item(self.table, expense.to_ddb_item())

    def delete_expense(
        self, user_email: str, date: dt.datetime, expense_id: str
    ) -> None:
        log.info(f"Deleting expense for user '{user_email}' from Expenses table")
        log.debug(
            f"Expense:\n{json.dumps({ 'user_email': user_email, 'date': date.strftime('%Y-%m-%d'), 'expense_id': expense_id}, indent=4)}"
        )
        self.ddb.delete_item(
            self.table,
            ExpensesTable._get_expenses_primary_key(user_email, date, expense_id),
        )

    @staticmethod
    def _get_expenses_table_name(domain: Domain) -> str:
        return ExpensesTable.EXPENSES_TABLE_NAME_FORMAT.format(domain=domain.value)

    @staticmethod
    def _get_expenses_by_user_query(user_email: str) -> dict:
        return {
            "user_email": {
                "AttributeValueList": [{"S": user_email}],
                "ComparisonOperator": "EQ",
            }
        }

    @staticmethod
    def _get_expenses_primary_key(
        user_email: str, date: dt.datetime, expense_id: str
    ) -> dict:
        return {
            "user_email": {"S": user_email},
            "date_uuid": {"S": f"{date.strftime('%Y-%m-%d')}#{expense_id}"},
        }

    @staticmethod
    def _get_expense_from_ddb_item(item: dict) -> Expense:
        date_uuid = item["date_uuid"]["S"]
        date_str, expense_id = date_uuid.split("#")
        date = dt.datetime.strptime(date_str, "%Y-%m-%d")
        return Expense(
            user_email=item["user_email"]["S"],
            date=date,
            vendor=item["vendor"]["S"],
            amount=float(item["amount"]["S"]),
            category=ExpenseCategory.from_string(item["category"]["S"]),
            expense_id=expense_id,
            date_uuid=date_uuid,
        )
