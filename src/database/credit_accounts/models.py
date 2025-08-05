import datetime as dt
import uuid
from dataclasses import dataclass


@dataclass
class CreditAccount:
    """
    WalterDB: CreditAccount model

    This model represents a user's credit account such
    as a credit card or a loan.
    """

    USER_ID_KEY_FORMAT = "USER#{user_id}"
    ACCOUNT_ID_KEY_FORMAT = "ACCOUNT#{account_id}"
    DEFAULT_LOGO_URL = "https://walterai-public-media-dev.s3.us-east-1.amazonaws.com/cash-accounts/default/logo.svg"

    user_id: str  # hash key
    account_id: str  # sort key
    bank_name: str
    account_name: str
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
        }

    @staticmethod
    def get_user_id_key(user_id: str) -> str:
        return CreditAccount.USER_ID_KEY_FORMAT.format(user_id=user_id)

    @staticmethod
    def get_account_id_key(account_id: str) -> str:
        return CreditAccount.ACCOUNT_ID_KEY_FORMAT.format(account_id=account_id)

    @classmethod
    def create_new_credit_account(
        cls,
        user_id: str,
        bank_name: str,
        account_name: str,
        account_last_four_numbers: str,
        balance: float,
    ):
        now = dt.datetime.now(dt.UTC)
        new_credit_account_id = str(uuid.uuid4())
        return CreditAccount(
            user_id=CreditAccount.get_user_id_key(user_id),
            account_id=CreditAccount.get_account_id_key(new_credit_account_id),
            bank_name=bank_name,
            account_name=account_name,
            account_last_four_numbers=account_last_four_numbers,
            balance=balance,
            created_at=now,
            updated_at=now,
        )
