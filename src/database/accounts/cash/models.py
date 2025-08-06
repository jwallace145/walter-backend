import datetime as dt
import uuid
from enum import Enum

from src.database.accounts.models import Account
from src.database.users.models import User


class CashAccountType(Enum):
    """
    WalterDB: CashAccountType Enum
    """

    CHECKING = "CHECKING"
    SAVINGS = "SAVINGS"
    MONEY_MARKET = "MONEY_MARKET"

    @classmethod
    def from_string(cls, account_type_str: str):
        for account_type in CashAccountType:
            if account_type_str.lower() == account_type.value.lower():
                return account_type
        raise ValueError(f"Unexpected cash account type '{account_type_str}'!")


class CashAccount(Account):
    """
    WalterDB: CashAccount Model

    This model represents a user's cash account such as a
    checking or savings account. Cash accounts are liquid
    and can be used to cover expenses. These differ from
    investments and retirement accounts which are less liquid
    and should under normal circumstances not be used for
    any expenses.
    """

    user_id: str  # hash key
    account_id: str  # sort key
    bank_name: str
    account_name: str
    account_type: CashAccountType
    account_last_four_numbers: str
    balance: float
    created_at: dt.datetime
    updated_at: dt.datetime

    def __init__(
        self,
        user_id: str,
        account_id: str,
        bank_name: str,
        account_name: str,
        account_last_four_numbers: str,
        balance: float,
        created_at: dt.datetime,
        updated_at: dt.datetime,
        account_type: CashAccountType,
        logo_url: str = Account.DEFAULT_LOGO_URL,
    ) -> None:
        super().__init__(
            user_id,
            account_id,
            bank_name,
            account_name,
            account_last_four_numbers,
            balance,
            created_at,
            updated_at,
            logo_url,
        )
        self.account_type = account_type

    def to_dict(self) -> dict:
        return {
            **self._get_common_attributes_dict(),
            "account_type": self.account_type.value,
        }

    def to_ddb_item(self) -> dict:
        return {
            **self._get_common_attributes_ddb_item(),
            "account_type": {"S": self.account_type.value},
        }

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
