from dataclasses import dataclass
import datetime as dt
from typing import List

from src.database.transactions.models import Transaction


@dataclass(frozen=True)
class CreateLinkTokenResponse:

    link_token: str
    expiration: dt.datetime
    request_id: str
    walter_user_id: str
    plaid_user_id: str

    def to_dict(self) -> dict:
        return {
            "link_token": self.link_token,
            "expiration": self.expiration.isoformat(),
            "request_id": self.request_id,
            "walter_user_id": self.walter_user_id,
            "plaid_user_id": self.plaid_user_id,
        }


@dataclass(frozen=True)
class ExchangePublicTokenResponse:

    public_token: str
    access_token: str
    item_id: str

    def to_dict(self) -> dict:
        return {
            "public_token": self.public_token,
            "access_token": self.access_token,
            "item_id": self.item_id,
        }


@dataclass(frozen=True)
class PlaidAccount:

    account_id: str
    balance: float
    name: str
    official_name: str
    subtype: str
    type: str


@dataclass(frozen=True)
class GetAccountsResponse:

    accounts: List[PlaidAccount]


@dataclass(frozen=True)
class SyncTransactionsResponse:

    cursor: str
    synced_at: dt.datetime
    added_transactions: List[Transaction]
    removed_transactions: List[Transaction]
    modified_transactions: List[Transaction]

    def to_dict(self) -> dict:
        return {
            "cursor": str,
            "synced_at": self.synced_at.isoformat(),
            "added": [transaction.to_dict() for transaction in self.added_transactions],
            "modified": [
                transaction.to_dict() for transaction in self.modified_transactions
            ],
            "removed": [
                transaction.to_dict() for transaction in self.removed_transactions
            ],
        }
