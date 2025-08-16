import datetime as dt

import pytest

from src.aws.dynamodb.client import WalterDDBClient
from src.database.transactions.models import (
    BankingTransactionSubType,
    BankTransaction,
    InvestmentTransaction,
    InvestmentTransactionSubType,
    TransactionCategory,
    TransactionType,
)
from src.database.transactions.table import TransactionsTable
from src.environment import Domain
from tst.constants import TRANSACTIONS_TABLE_NAME


@pytest.fixture
def transactions_table(ddb_client) -> TransactionsTable:
    ddb = WalterDDBClient(ddb_client)
    return TransactionsTable(ddb=ddb, domain=Domain.TESTING)


def test_table_name_format(transactions_table: TransactionsTable):
    assert transactions_table.table_name == TRANSACTIONS_TABLE_NAME


def test_get_transaction_investment(transactions_table: TransactionsTable):
    # Seeded by MockDDB from tst/database/data/transactions.jsonl
    account_id = "acct-002"
    txn_id = "investment-txn-001"
    date = dt.datetime(2025, 8, 1)

    txn = transactions_table.get_transaction(account_id, date, txn_id)
    assert isinstance(txn, InvestmentTransaction)
    assert txn.transaction_id == txn_id
    assert txn.account_id == account_id
    assert txn.transaction_type == TransactionType.INVESTMENT
    assert txn.transaction_subtype == InvestmentTransactionSubType.BUY
    assert txn.transaction_category == TransactionCategory.INVESTMENT
    assert txn.security_id == "sec-nasdaq-aapl"
    assert txn.quantity == pytest.approx(10.0)
    assert txn.price_per_share == pytest.approx(100.0)
    assert txn.transaction_amount == pytest.approx(1000.0)
    # Ensure the stored sort-key format is preserved (YYYY-MM-DD#id)
    assert txn.transaction_date.startswith("2025-08-01#")


def test_get_transaction_bank(transactions_table: TransactionsTable):
    account_id = "acct-003"
    txn_id = "bank-txn-001"
    date = dt.datetime(2025, 8, 5)

    txn = transactions_table.get_transaction(account_id, date, txn_id)
    assert isinstance(txn, BankTransaction)
    assert txn.transaction_id == txn_id
    assert txn.account_id == account_id
    assert txn.transaction_type == TransactionType.BANKING
    assert txn.transaction_subtype == BankingTransactionSubType.DEBIT
    assert txn.transaction_category == TransactionCategory.RESTAURANTS
    assert txn.merchant_name == "Starbucks"
    assert txn.transaction_amount == pytest.approx(5.0)
    assert txn.transaction_date.startswith("2025-08-05#")


def test_get_transactions_date_range(transactions_table: TransactionsTable):
    # For acct-003 we have entries on 2025-08-05 and 2025-08-06 (three total)
    account_id = "acct-003"
    start = dt.datetime(2025, 8, 5)
    end = dt.datetime(2025, 8, 6)

    txns = transactions_table.get_transactions(account_id, start, end)
    assert isinstance(txns, list)
    ids = {t.transaction_id for t in txns}
    assert ids == {"bank-txn-001", "bank-txn-002", "bank-txn-003"}
    assert all(isinstance(t, BankTransaction) for t in txns)


def test_get_transactions_by_account(transactions_table: TransactionsTable):
    # acct-002 has four investment transactions in the seed file
    txns = transactions_table.get_transactions_by_account("acct-002")
    assert isinstance(txns, list)
    assert len(txns) == 4
    assert all(isinstance(t, InvestmentTransaction) for t in txns)


def test_put_and_get_transaction(transactions_table: TransactionsTable):
    # Create and put a new bank transaction
    date = dt.datetime(2025, 8, 7)
    new_txn = BankTransaction.create(
        account_id="acct-003",
        user_id="user-002",
        transaction_type=TransactionType.BANKING,
        transaction_subtype=BankingTransactionSubType.DEBIT,
        transaction_category=TransactionCategory.RESTAURANTS,
        transaction_date=date,
        transaction_amount=12.34,
        merchant_name="Chipotle",
    )

    created = transactions_table.put_transaction(new_txn)
    assert isinstance(created, BankTransaction)
    # Retrieve it back using its generated id and the same date
    fetched = transactions_table.get_transaction(
        "acct-003", date, created.transaction_id
    )
    assert isinstance(fetched, BankTransaction)
    assert fetched.transaction_id == created.transaction_id
    assert fetched.account_id == "acct-003"
    assert fetched.merchant_name == "Chipotle"
    assert fetched.transaction_amount == pytest.approx(12.34)


def test_delete_transaction(transactions_table: TransactionsTable):
    # Delete an existing seeded transaction and check it's gone
    account_id = "acct-003"
    txn_id = "bank-txn-002"
    date = dt.datetime(2025, 8, 6)

    # Ensure it exists first
    assert transactions_table.get_transaction(account_id, date, txn_id) is not None

    # Delete and verify removal
    transactions_table.delete_transaction(account_id, date, txn_id)
    assert transactions_table.get_transaction(account_id, date, txn_id) is None
