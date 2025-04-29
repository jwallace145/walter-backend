import datetime as dt
import uuid
from dataclasses import dataclass
from enum import Enum


class TransactionCategory(Enum):
    """
    Transaction Category Enum
    """

    BILLS = "Bills"
    ENTERTAINMENT = "Entertainment"
    GROCERIES = "Groceries"
    HEALTH_AND_WELLNESS = "Health and Wellness"
    HOBBIES = "Hobbies"
    HOUSING = "Housing"
    INCOME = "Income"
    INSURANCE = "Insurance"
    MERCHANDISE = "Merchandise"
    RESTAURANTS = "Restaurants"
    SHOPPING = "Shopping"
    SUBSCRIPTIONS = "Subscriptions"
    TRANSPORTATION = "Transportation"
    TRAVEL = "Travel"

    @staticmethod
    def from_string(category_str: str):
        for category in TransactionCategory:
            # lower case category and replace chars with
            # friendly chars for ease of parsing
            category_str = category_str.lower().strip()
            category_str = category_str.replace("&", "and")
            if category_str == category.value.lower():
                return category
        raise ValueError(
            f"Invalid expense category '{category_str}'! Valid expense categories: {[category.value for category in TransactionCategory]}"
        )


@dataclass
class Transaction:
    """
    Transaction Model

    This model represents a user transaction. A user
    transaction can be an expense or income. Expenses
    subtract money from the user's total net worth while
    income adds money to the user's total net worth.
    """

    DATE_FORMAT = "%Y-%m-%d"

    user_id: str  # hash key
    date: dt.datetime
    vendor: str
    amount: float
    category: TransactionCategory

    transaction_id: str = None  # set during post init
    date_uuid: str = (
        None  # sort key -> format: `<date>#<transaction_id>` set during post init
    )

    def __post_init__(self):
        if self.transaction_id is None:
            self.transaction_id = str(uuid.uuid4())

        if self.date_uuid is None:
            datestamp = self.date.strftime(Transaction.DATE_FORMAT)
            self.date_uuid = f"{datestamp}#{self.transaction_id}"

    def to_dict(self) -> dict:
        return {
            "date": self.date.strftime(Transaction.DATE_FORMAT),
            "transaction_id": self.transaction_id,
            "vendor": self.vendor,
            "amount": self.amount,
            "category": self.category.value,
        }

    def to_ddb_item(self) -> dict:
        return {
            "user_id": {
                "S": self.user_id,
            },
            "date_uuid": {
                "S": self.date_uuid,
            },
            "vendor": {
                "S": self.vendor,
            },
            "amount": {
                "S": str(self.amount),
            },
            "category": {
                "S": self.category.value,
            },
        }

    def is_expense(self) -> bool:
        return self.amount < 0

    def is_income(self) -> bool:
        return self.amount > 0
