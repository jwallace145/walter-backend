from dataclasses import dataclass
from datetime import datetime, timezone

from src.database.transactions.models import (
    BankingTransactionSubType,
    BankTransaction,
    TransactionCategory,
    TransactionType,
)
from src.plaid.models import (
    CreateLinkTokenResponse,
    ExchangePublicTokenResponse,
    SyncTransactionsResponse,
)

UBER_TXN = BankTransaction.create(
    account_id="acct-001",
    user_id="user-001",
    transaction_type=TransactionType.BANKING,
    transaction_subtype=BankingTransactionSubType.DEBIT,
    transaction_category=TransactionCategory.TRAVEL,
    transaction_date=datetime.strptime("2025-08-30", "%Y-%m-%d"),
    transaction_amount=6.33,
    merchant_name="Uber",
    plaid_transaction_id="plaid-txn-001",
    plaid_account_id="plaid-acct-001",
)


@dataclass
class MockPlaidClient:
    def create_link_token(self, user_id: str) -> CreateLinkTokenResponse:
        return CreateLinkTokenResponse(
            request_id="test-request-id",
            user_id=user_id,
            link_token="test-link-token",
            expiration=datetime.now(timezone.utc),
        )

    def sync_transactions(
        self, user_id: str, token: str, cursor: str
    ) -> SyncTransactionsResponse:
        return SyncTransactionsResponse(
            cursor="test-cursor",
            synced_at=datetime.now(timezone.utc),
            added_transactions=[UBER_TXN],
            removed_transactions=[],
            modified_transactions=[],
        )

    def exchange_public_token(self, public_token: str) -> ExchangePublicTokenResponse:
        return ExchangePublicTokenResponse(
            public_token=public_token,
            access_token="test-access-token",
            item_id="test-item-id",
        )
