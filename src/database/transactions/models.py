import random
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Union


class TransactionType(Enum):
    """Transaction Types"""

    INVESTMENT = "investment"
    BANKING = "banking"

    @classmethod
    def from_string(cls, transaction_type_str: str):
        for transaction_type in TransactionType:
            if transaction_type.name.lower() == transaction_type_str.lower():
                return transaction_type
        raise ValueError(f"Invalid transaction type '{transaction_type_str}'!")


class InvestmentTransactionSubType(Enum):
    """Investment Transaction Sub Types"""

    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"

    @classmethod
    def from_string(cls, sub_type_str: str):
        for sub_type in InvestmentTransactionSubType:
            if sub_type.name.lower() == sub_type_str.lower():
                return sub_type
        raise ValueError(f"Invalid investment transaction sub type '{sub_type_str}'!")


class BankingTransactionSubType(Enum):
    """Banking Transaction Sub Types"""

    CREDIT = "credit"
    DEBIT = "debit"
    TRANSFER = "transfer"
    INTEREST = "interest"

    @classmethod
    def from_string(cls, sub_type_str: str):
        for sub_type in BankingTransactionSubType:
            if sub_type.name.lower() == sub_type_str.lower():
                return sub_type
        raise ValueError(f"Invalid banking transaction sub type '{sub_type_str}'!")


TransactionSubType = Union[InvestmentTransactionSubType, BankingTransactionSubType]


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
    INVESTMENT = "Investment"

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


class Transaction(ABC):
    """Transaction Model"""

    def __init__(
        self,
        transaction_id: str,
        account_id: str,
        user_id: str,
        transaction_type: TransactionType,
        transaction_subtype: TransactionSubType,
        transaction_category: TransactionCategory,
        transaction_date: datetime,
        transaction_amount: float,
    ) -> None:
        self.transaction_id = transaction_id
        self.account_id = account_id
        self.user_id = user_id
        self.transaction_type = transaction_type
        self.transaction_subtype = transaction_subtype
        self.transaction_category = transaction_category
        self.transaction_date = (
            f"{transaction_date.strftime('%Y-%m-%d')}#{transaction_id}"
        )
        self.transaction_amount = transaction_amount

    def _get_common_attributes_dict(self) -> dict:
        return {
            "transaction_id": self.transaction_id,
            "account_id": self.account_id,
            "user_id": self.user_id,
            "transaction_type": self.transaction_type.value,
            "transaction_subtype": self.transaction_subtype.value,
            "transaction_category": self.transaction_category.value,
            "transaction_date": self.transaction_date,
            "transaction_amount": self.transaction_amount,
        }

    def _get_common_attributes_ddb_item(self) -> dict:
        return {
            "transaction_id": {"S": self.transaction_id},
            "account_id": {"S": self.account_id},
            "user_id": {"S": self.user_id},
            "transaction_type": {"S": self.transaction_type.value},
            "transaction_subtype": {"S": self.transaction_subtype.value},
            "transaction_category": {"S": self.transaction_category.value},
            "transaction_date": {"S": self.transaction_date},
            "transaction_amount": {"N": str(self.transaction_amount)},
        }

    def is_income(self) -> bool:
        if self.transaction_type == TransactionType.BANKING:
            return self.transaction_subtype in [
                BankingTransactionSubType.CREDIT,
                BankingTransactionSubType.INTEREST,
            ]
        return False

    def is_expense(self) -> bool:
        if self.transaction_type == TransactionType.BANKING:
            return self.transaction_subtype in [BankingTransactionSubType.DEBIT]
        return False

    @abstractmethod
    def to_dict(self) -> dict:
        pass

    @abstractmethod
    def to_ddb_item(self) -> dict:
        pass

    @staticmethod
    def _generate_id(prefix: str) -> str:
        timestamp_part = str(int(datetime.now(timezone.utc).timestamp()))[-6:]
        random_part = str(random.randint(1000, 9999))
        return f"{prefix}-txn-{timestamp_part}{random_part}"


class InvestmentTransaction(Transaction):
    """Investment Transaction Model"""

    def __init__(
        self,
        transaction_id: str,
        account_id: str,
        user_id: str,
        transaction_type: TransactionType,
        transaction_subtype: TransactionSubType,
        transaction_category: TransactionCategory,
        transaction_date: datetime,
        transaction_amount: float,
        security_id: str,
        quantity: float,
        price_per_share: float,
    ) -> None:
        super().__init__(
            transaction_id,
            account_id,
            user_id,
            transaction_type,
            transaction_subtype,
            transaction_category,
            transaction_date,
            transaction_amount,
        )
        self.security_id = security_id
        self.quantity = quantity
        self.price_per_share = price_per_share

    def to_dict(self) -> dict:
        return {
            **self._get_common_attributes_dict(),
            "security_id": self.security_id,
            "quantity": self.quantity,
            "price_per_share": self.price_per_share,
        }

    def to_ddb_item(self) -> dict:
        return {
            **self._get_common_attributes_ddb_item(),
            "security_id": {
                "S": self.security_id,
            },
            "quantity": {
                "N": str(self.quantity),
            },
            "price_per_share": {
                "N": str(self.price_per_share),
            },
        }

    @classmethod
    def create(
        cls,
        account_id: str,
        user_id: str,
        date: datetime,
        security_id: str,
        transaction_type: TransactionType,
        transaction_subtype: TransactionSubType,
        transaction_category: TransactionCategory,
        quantity: float,
        price_per_share: float,
    ):
        return InvestmentTransaction(
            transaction_id=Transaction._generate_id("investment"),
            account_id=account_id,
            user_id=user_id,
            transaction_type=transaction_type,
            transaction_subtype=transaction_subtype,
            transaction_category=transaction_category,
            transaction_date=date,
            transaction_amount=quantity * price_per_share,
            security_id=security_id,
            quantity=quantity,
            price_per_share=price_per_share,
        )

    @classmethod
    def from_ddb_item(cls, ddb_item: dict):
        return InvestmentTransaction(
            transaction_id=ddb_item["transaction_id"]["S"],
            account_id=ddb_item["account_id"]["S"],
            user_id=ddb_item["user_id"]["S"],
            transaction_type=TransactionType.from_string(
                ddb_item["transaction_type"]["S"]
            ),
            transaction_category=TransactionCategory.from_string(
                ddb_item["transaction_category"]["S"]
            ),
            transaction_subtype=InvestmentTransactionSubType.from_string(
                ddb_item["transaction_subtype"]["S"]
            ),
            transaction_date=datetime.strptime(
                ddb_item["transaction_date"]["S"].split("#")[0], "%Y-%m-%d"
            ),
            transaction_amount=float(ddb_item["transaction_amount"]["N"]),
            security_id=ddb_item["security_id"]["S"],
            quantity=float(ddb_item["quantity"]["N"]),
            price_per_share=float(ddb_item["price_per_share"]["N"]),
        )


class BankTransaction(Transaction):
    """Bank Transaction Model"""

    def __init__(
        self,
        transaction_id: str,
        account_id: str,
        user_id: str,
        transaction_type: TransactionType,
        transaction_subtype: TransactionSubType,
        transaction_category: TransactionCategory,
        transaction_date: datetime,
        transaction_amount: float,
        merchant_name: str,
    ) -> None:
        super().__init__(
            transaction_id,
            account_id,
            user_id,
            transaction_type,
            transaction_subtype,
            transaction_category,
            transaction_date,
            transaction_amount,
        )
        self.merchant_name = merchant_name

    def to_dict(self) -> dict:
        return {
            **self._get_common_attributes_dict(),
            "merchant_name": self.merchant_name,
        }

    def to_ddb_item(self) -> dict:
        return {
            **self._get_common_attributes_ddb_item(),
            "merchant_name": {"S": self.merchant_name},
        }

    @classmethod
    def create(
        cls,
        account_id: str,
        user_id: str,
        transaction_type: TransactionType,
        transaction_subtype: TransactionSubType,
        transaction_category: TransactionCategory,
        transaction_date: datetime,
        transaction_amount: float,
        merchant_name: str,
    ):
        return BankTransaction(
            transaction_id=Transaction._generate_id("bank"),
            account_id=account_id,
            user_id=user_id,
            transaction_type=transaction_type,
            transaction_subtype=transaction_subtype,
            transaction_category=transaction_category,
            transaction_date=transaction_date,
            transaction_amount=transaction_amount,
            merchant_name=merchant_name,
        )

    @classmethod
    def from_ddb_item(cls, ddb_item: dict):
        return BankTransaction(
            transaction_id=ddb_item["transaction_id"]["S"],
            account_id=ddb_item["account_id"]["S"],
            user_id=ddb_item["user_id"]["S"],
            transaction_type=TransactionType.from_string(
                ddb_item["transaction_type"]["S"]
            ),
            transaction_subtype=BankingTransactionSubType.from_string(
                ddb_item["transaction_subtype"]["S"]
            ),
            transaction_category=TransactionCategory.from_string(
                ddb_item["transaction_category"]["S"]
            ),
            transaction_date=datetime.strptime(
                ddb_item["transaction_date"]["S"].split("#")[0], "%Y-%m-%d"
            ),
            transaction_amount=float(ddb_item["transaction_amount"]["N"]),
            merchant_name=ddb_item["merchant_name"]["S"],
        )
