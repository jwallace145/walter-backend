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

    @classmethod
    def from_string(cls, category_str: str):
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
    account_id: str  # foreign key to accounts table
    vendor: str
    amount: float
    category: TransactionCategory

    transaction_id: str = None  # set during post init
    date_uuid: str = (
        None  # sort key -> format: `<date>#<transaction_id>` set during post init
    )
    reviewed: bool = (
        False  # on transaction creation, transactions are considered "not reviewed"
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
            "account_id": self.account_id,
            "transaction_id": self.transaction_id,
            "vendor": self.vendor,
            "amount": self.amount,
            "category": self.category.value,
            "reviewed": self.reviewed,
        }

    def to_ddb_item(self) -> dict:
        return {
            "user_id": {
                "S": self.user_id,
            },
            "account_id": {
                "S": self.account_id,
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
            "reviewed": {
                "BOOL": self.reviewed,
            },
        }

    def is_reviewed(self) -> bool:
        return self.reviewed

    def is_expense(self) -> bool:
        return self.amount < 0

    def is_income(self) -> bool:
        return self.amount > 0

    @classmethod
    def from_ddb_item(cls, item: dict):
        date_uuid = item["date_uuid"]["S"]
        date_str, transaction_id = date_uuid.split("#")
        date = dt.datetime.strptime(date_str, "%Y-%m-%d")
        amount = float(item["amount"]["S"])
        category = TransactionCategory.from_string(item["category"]["S"])
        return Transaction(
            user_id=item["user_id"]["S"],
            date=date,
            vendor=item["vendor"]["S"],
            account_id=item["account_id"]["S"],
            amount=amount,
            category=category,
            transaction_id=transaction_id,
            date_uuid=date_uuid,
            reviewed=item["reviewed"]["BOOL"],
        )
