import uuid
from dataclasses import dataclass

from enum import Enum
import datetime as dt


class ExpenseCategory(Enum):
    """
    Expense Category Enum
    """

    BILLS = "bills"
    ENTERTAINMENT = "entertainment"
    GROCERIES = "groceries"
    HEALTH_AND_WELLNESS = "health_and_wellness"
    HOBBIES = "hobbies"
    HOUSING = "housing"
    INSURANCE = "insurance"
    MERCHANDISE = "merchandise"
    RESTAURANTS = "restaurants"
    SHOPPING = "shopping"
    SUBSCRIPTIONS = "subscriptions"
    TRANSPORTATION = "transportation"
    TRAVEL = "travel"

    @staticmethod
    def from_string(category_str: str):
        for category in ExpenseCategory:
            # lower case category and replace chars with
            # friendly chars for ease of parsing
            category_str = category_str.lower().strip()
            category_str = category_str.replace(" ", "_")
            category_str = category_str.replace("&", "and")
            if category_str == category.value:
                return category
        raise ValueError(
            f"Invalid expense category '{category_str}'! Valid expense categories: {[category.value for category in ExpenseCategory]}"
        )


@dataclass
class Expense:
    """
    Expense Model

    This class represents the model for an Expense item.
    Users track their expenses by creating Expense items
    that are then stored in WalterDB.
    """

    DATE_FORMAT = "%Y-%m-%d"

    user_email: str  # hash key
    date: dt.datetime
    vendor: str
    amount: float
    category: ExpenseCategory

    expense_id: str = None  # set during post init
    date_uuid: str = None  # sort key -> format: `<date>#<uuid>` set during post init

    def __post_init__(self):
        if self.expense_id is None:
            self.expense_id = str(uuid.uuid4())[:8]

        if self.date_uuid is None:
            datestamp = self.date.strftime(Expense.DATE_FORMAT)
            self.date_uuid = f"{datestamp}#{self.expense_id}"

    def to_dict(self) -> dict:
        return {
            "user_email": self.user_email,
            "date": self.date.strftime(Expense.DATE_FORMAT),
            "expense_id": self.expense_id,
            "vendor": self.vendor.lower(),
            "amount": self.amount,
            "category": self.category.value,
        }

    def to_ddb_item(self) -> dict:
        return {
            "user_email": {
                "S": self.user_email,
            },
            "date_uuid": {
                "S": self.date_uuid,
            },
            "vendor": {
                "S": self.vendor.lower(),
            },
            "amount": {
                "S": str(self.amount),
            },
            "category": {
                "S": self.category.value,
            },
        }
