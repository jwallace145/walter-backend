from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import random
from typing import Optional


class AccountType(Enum):
    """Account Types"""

    DEPOSITORY = "depository"
    CREDIT = "credit"
    INVESTMENT = "investment"
    LOAN = "loan"

    @classmethod
    def from_string(cls, account_type_str: str):
        for account_type in AccountType:
            if account_type.name.lower() == account_type_str.lower():
                return account_type
        raise ValueError(f"Invalid account type '{account_type_str}'!")


@dataclass
class Account:
    """Account Model"""

    DEFAULT_LOGO_URL = "https://walterai-public-media-dev.s3.us-east-1.amazonaws.com/cash-accounts/default/logo.svg"

    account_id: str
    user_id: str
    account_type: AccountType
    account_subtype: str
    institution_name: str
    account_name: str
    account_mask: str
    balance: float
    balance_last_updated_at: datetime
    created_at: datetime
    updated_at: datetime
    plaid_account_id: Optional[str] = None
    plaid_item_id: Optional[str] = None
    plaid_last_sync_at: Optional[datetime] = None
    logo_url: str = DEFAULT_LOGO_URL

    def to_dict(self) -> dict:
        return {
            "account_id": self.account_id,
            "user_id": self.user_id,
            "account_type": self.account_type.name.lower(),
            "account_subtype": self.account_subtype,
            "institution_name": self.institution_name,
            "account_name": self.account_name,
            "account_mask": self.account_mask,
            "balance": self.balance,
            "balance_last_updated_at": self.balance_last_updated_at.isoformat(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "plaid_account_id": self.plaid_account_id,
            "plaid_item_id": self.plaid_item_id,
            "plaid_last_sync_at": (
                self.plaid_last_sync_at.isoformat() if self.plaid_last_sync_at else None
            ),
            "logo_url": self.logo_url,
        }

    def to_ddb_item(self) -> dict:
        ddb_item = {
            "user_id": {
                "S": self.user_id,
            },
            "account_id": {
                "S": self.account_id,
            },
            "account_type": {
                "S": self.account_type.name.lower(),
            },
            "account_subtype": {
                "S": self.account_subtype,
            },
            "institution_name": {
                "S": self.institution_name,
            },
            "account_name": {
                "S": self.account_name,
            },
            "account_mask": {
                "S": self.account_mask,
            },
            "balance": {
                "N": str(self.balance),
            },
            "balance_last_updated_at": {
                "S": self.balance_last_updated_at.isoformat(),
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

        # add optional fields to return item
        if self.plaid_account_id:
            ddb_item["plaid_account_id"] = {
                "S": self.plaid_account_id,
            }
        if self.plaid_item_id:
            ddb_item["plaid_item_id"] = {
                "S": self.plaid_item_id,
            }
        if self.plaid_last_sync_at:
            ddb_item["plaid_last_sync_at"] = {"S": self.plaid_last_sync_at.isoformat()}

        return ddb_item

    @staticmethod
    def generate_account_id() -> str:
        timestamp_part = str(int(datetime.now(timezone.utc).timestamp()))[-6:]
        random_part = str(random.randint(1000, 9999))
        return f"acct-{timestamp_part}{random_part}"

    @classmethod
    def create_new_account(
        cls,
        user_id: str,
        account_type: str,
        account_subtype: str,
        institution_name: str,
        account_name: str,
        account_mask: str,
        balance: float,
    ):
        now = datetime.now(timezone.utc)
        return Account(
            account_id=Account.generate_account_id(),
            user_id=user_id,
            account_type=AccountType.from_string(account_type),
            account_subtype=account_subtype,
            institution_name=institution_name,
            account_name=account_name,
            account_mask=account_mask,
            balance=balance,
            balance_last_updated_at=now,
            created_at=now,
            updated_at=now,
        )

    @classmethod
    def from_ddb_item(cls, ddb_item: dict):
        plaid_last_sync_at = None
        if ddb_item.get("plaid_last_sync_at", {}).get("S"):
            plaid_last_sync_at = datetime.fromisoformat(
                ddb_item["plaid_last_sync_at"]["S"]
            )
        return Account(
            user_id=ddb_item["user_id"]["S"],
            account_id=ddb_item["account_id"]["S"],
            account_type=AccountType.from_string(ddb_item["account_type"]["S"]),
            account_subtype=ddb_item["account_subtype"]["S"],
            institution_name=ddb_item["institution_name"]["S"],
            account_name=ddb_item["account_name"]["S"],
            account_mask=ddb_item["account_mask"]["S"],
            balance=float(ddb_item["balance"]["N"]),
            balance_last_updated_at=datetime.fromisoformat(
                ddb_item["balance_last_updated_at"]["S"]
            ),
            created_at=datetime.fromisoformat(ddb_item["created_at"]["S"]),
            updated_at=datetime.fromisoformat(ddb_item["updated_at"]["S"]),
            logo_url=ddb_item["logo_url"]["S"],
            plaid_account_id=ddb_item.get("plaid_account_id", {}).get("S"),
            plaid_item_id=ddb_item.get("plaid_item_id", {}).get("S"),
            plaid_last_sync_at=plaid_last_sync_at,
        )
