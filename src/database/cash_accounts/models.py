import datetime as dt
import uuid
from dataclasses import dataclass
from enum import Enum

from src.database.users.models import User


class CashAccountType(Enum):
    """
    WalterDB: CashAccountType Enum
    """

    CHECKING = "CHECKING"
    SAVINGS = "SAVINGS"

    @classmethod
    def from_string(cls, account_type_str: str):
        for account_type in CashAccountType:
            if account_type_str.lower() == account_type.value.lower():
                return account_type
        raise ValueError(f"Unexpected cash account type '{account_type_str}'!")


@dataclass
class CashAccount:
    """
    WalterDB: CashAccount Model

    This model represents a user's cash account such as a
    checking or savings account. Cash accounts are liquid
    and can be used to cover expenses. These differ from
    investments and retirement accounts which are less liquid
    and should under normal circumstances not be used for
    any expenses.
    """

    USER_ID_KEY_FORMAT = "USER#{user_id}"
    ACCOUNT_ID_KEY_FORMAT = "ACCOUNT#{account_id}"
    DEFAULT_LOGO_URL = "https://walterai-public-media-dev.s3.us-east-1.amazonaws.com/cash-accounts/default/logo.svg"

    user_id: str  # hash key
    account_id: str  # sort key
    bank_name: str
    account_name: str
    account_type: CashAccountType
    account_last_four_numbers: str
    balance: float
    created_at: dt.datetime
    updated_at: dt.datetime
    logo_url: str = DEFAULT_LOGO_URL

    def to_dict(self) -> dict:
        return {
            "account_id": self.account_id.split("#")[1],
            "bank_name": self.bank_name,
            "account_name": self.account_name,
            "account_type": self.account_type.value,
            "account_last_four_numbers": self.account_last_four_numbers,
            "balance": self.balance,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "logo_url": self.logo_url,
        }

    def to_ddb_item(self) -> dict:
        return {
            "user_id": {
                "S": self.user_id,
            },
            "account_id": {
                "S": self.account_id,
            },
            "bank_name": {
                "S": self.bank_name,
            },
            "account_name": {
                "S": self.account_name,
            },
            "account_type": {
                "S": self.account_type.value,
            },
            "account_last_four_numbers": {
                "S": self.account_last_four_numbers,
            },
            "balance": {
                "N": str(self.balance),
            },
            "created_at": {
                "S": self.created_at.isoformat(),
            },
            "updated_at": {
                "S": self.updated_at.isoformat(),
            },
            "logo_url": {
                "S": self.logo_url,
            },
        }

    def get_account_id(self) -> str:
        return self.account_id.split("#")[1]

    @staticmethod
    def get_user_id_key(user_id: str) -> str:
        return CashAccount.USER_ID_KEY_FORMAT.format(user_id=user_id)

    @staticmethod
    def get_account_id_key(account_id: str) -> str:
        return CashAccount.ACCOUNT_ID_KEY_FORMAT.format(account_id=account_id)

    @classmethod
    def create_new_account(
        cls,
        user: User,
        bank_name: str,
        account_name: str,
        account_type: CashAccountType,
        account_last_four_numbers: str,
        balance: float,
    ):
        """
        Create a new cash account with the given parameters.

        Use this class method to create a new cash account that does
        not already exist. This method differs from the `create_account`
        class method as that method is meant to marshal the given parameters
        of an existing cash account into the `CashAccount` model.

        Args:
            user: The user that owns the new cash account.
            bank_name: The name of the bank that owns the new cash account.
            account_name: The account name of the new cash account.
            account_type: The type of the new cash account.
            account_last_four_numbers: The new cash account's last four numbers.
            balance: The starting balance of the new cash account.

        Returns:
            (CashAccount): The new cash account with a unique ID.
        """
        # create a new unique identifier since its a new cash acct
        new_account_id = str(uuid.uuid4())
        return CashAccount.create_account(
            user=user,
            account_id=new_account_id,
            bank_name=bank_name,
            account_name=account_name,
            account_type=account_type,
            account_last_four_numbers=account_last_four_numbers,
            balance=balance,
        )

    @classmethod
    def create_account(
        cls,
        user: User,
        account_id: str,
        bank_name: str,
        account_name: str,
        account_type: CashAccountType,
        account_last_four_numbers: str,
        balance: float,
    ):
        now = dt.datetime.now(dt.UTC)
        return CashAccount(
            user_id=CashAccount.get_user_id_key(user.user_id),
            account_id=CashAccount.get_account_id_key(account_id),
            bank_name=bank_name,
            account_name=account_name,
            account_type=account_type,
            account_last_four_numbers=account_last_four_numbers,
            balance=balance,
            created_at=now,
            updated_at=now,
        )

    @classmethod
    def get_account_from_ddb_item(cls, ddb_item: dict):
        return CashAccount(
            user_id=ddb_item["user_id"]["S"],
            account_id=ddb_item["account_id"]["S"],
            bank_name=ddb_item["bank_name"]["S"],
            account_name=ddb_item["account_name"]["S"],
            account_type=CashAccountType.from_string(ddb_item["account_type"]["S"]),
            account_last_four_numbers=ddb_item["account_last_four_numbers"]["S"],
            balance=float(ddb_item["balance"]["N"]),
            created_at=dt.datetime.fromisoformat(ddb_item["created_at"]["S"]),
            updated_at=dt.datetime.fromisoformat(ddb_item["updated_at"]["S"]),
            logo_url=ddb_item["logo_url"]["S"],
        )
