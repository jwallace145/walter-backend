import datetime as dt
from abc import ABC, abstractmethod


class Account(ABC):
    """
    WalterDB: Account Model

    The base abstract model class for all account types.
    """

    USER_ID_KEY_FORMAT = "USER#{user_id}"
    ACCOUNT_ID_KEY_FORMAT = "ACCOUNT#{account_id}"
    DEFAULT_LOGO_URL = "https://walterai-public-media-dev.s3.us-east-1.amazonaws.com/cash-accounts/default/logo.svg"

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
        logo_url: str = DEFAULT_LOGO_URL,
    ) -> None:
        self.user_id = user_id
        self.account_id = account_id
        self.bank_name = bank_name
        self.account_name = account_name
        self.account_last_four_numbers = account_last_four_numbers
        self.balance = balance
        self.created_at = created_at
        self.updated_at = updated_at
        self.logo_url = logo_url

    def _get_common_attributes_dict(self) -> dict:
        return {
            "account_id": Account.get_key_value(self.account_id),
            "bank_name": self.bank_name,
            "account_name": self.account_name,
            "account_last_four_numbers": self.account_last_four_numbers,
            "balance": self.balance,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "logo_url": self.logo_url,
        }

    def _get_common_attributes_ddb_item(self) -> dict:
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

    @abstractmethod
    def to_dict(self) -> dict:
        pass

    @abstractmethod
    def to_ddb_item(self) -> dict:
        pass

    @staticmethod
    def get_key_value(key: str) -> str:
        return key.split("#")[1]

    @staticmethod
    def get_user_id_key(user_id: str) -> str:
        return Account.USER_ID_KEY_FORMAT.format(user_id=user_id)

    @staticmethod
    def get_account_id_key(account_id: str) -> str:
        return Account.ACCOUNT_ID_KEY_FORMAT.format(account_id=account_id)
