import datetime as dt
from dataclasses import dataclass
from typing import List

from src.database.transactions.models import Transaction


@dataclass(frozen=True)
class CreateLinkTokenResponse:

    request_id: str
    user_id: str
    link_token: str
    expiration: dt.datetime

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "link_token": self.link_token,
            "expiration": self.expiration.isoformat(),
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
