import datetime as dt

import pytest

from src.aws.dynamodb.client import WalterDDBClient
from src.database.transactions.models import Transaction, TransactionCategory
from src.database.transactions.table import TransactionsTable
from src.environment import Domain
from tst.constants import TRANSACTIONS_TABLE_NAME


@pytest.fixture
def transactions_table(ddb_client) -> TransactionsTable:
    ddb = WalterDDBClient(ddb_client)
    return TransactionsTable(ddb=ddb, domain=Domain.TESTING)


def test_table_name_format(transactions_table: TransactionsTable):
    # Ensure the table name follows the expected format for the testing domain
    assert transactions_table.table == TRANSACTIONS_TABLE_NAME


def test_get_transaction_seeded_items(transactions_table: TransactionsTable):
    # Seeded by MockDDB from tst/database/data/transactions.jsonl
    t1 = transactions_table.get_transaction(
        user_id="user-001",
        date=dt.datetime.strptime("2025-08-01", "%Y-%m-%d"),
        transaction_id="001",
    )
    assert isinstance(t1, Transaction)
    assert t1.user_id == "user-001"
    assert t1.account_id == "acct-001"
    assert t1.vendor == "Starbucks"
    assert t1.amount == pytest.approx(5.0)
    assert t1.category == TransactionCategory.RESTAURANTS
    assert t1.reviewed is True

    t2 = transactions_table.get_transaction(
        user_id="user-001",
        date=dt.datetime.strptime("2025-08-03", "%Y-%m-%d"),
        transaction_id="004",
    )
    assert isinstance(t2, Transaction)
    assert t2.vendor == "Car Insurance"
    assert t2.category == TransactionCategory.INSURANCE
    assert t2.reviewed is False


def test_get_transaction_not_found(transactions_table: TransactionsTable):
    result = transactions_table.get_transaction(
        user_id="user-001",
        date=dt.datetime.strptime("2025-08-05", "%Y-%m-%d"),
        transaction_id="999",
    )
    assert result is None


def test_get_transactions_date_range(transactions_table: TransactionsTable):
    # Full range covering all seeded transactions
    txns = transactions_table.get_transactions(
        user_id="user-001",
        start_date=dt.datetime.strptime("2025-08-01", "%Y-%m-%d"),
        end_date=dt.datetime.strptime("2025-08-03", "%Y-%m-%d"),
    )
    assert isinstance(txns, list)
    assert len(txns) == 4
    # Ensure sorted descending by date
    dates = [t.date for t in txns]
    assert dates == sorted(dates, reverse=True)

    # Narrower range (first two days)
    txns2 = transactions_table.get_transactions(
        user_id="user-001",
        start_date=dt.datetime.strptime("2025-08-01", "%Y-%m-%d"),
        end_date=dt.datetime.strptime("2025-08-02", "%Y-%m-%d"),
    )
    assert len(txns2) == 3
    dates2 = [t.date for t in txns2]
    assert max(dates2) <= dt.datetime.strptime("2025-08-02", "%Y-%m-%d")
    assert min(dates2) >= dt.datetime.strptime("2025-08-01", "%Y-%m-%d")


def test_put_and_delete_transaction(transactions_table: TransactionsTable):
    # Create and put a new transaction for the seeded user/account
    new_txn = Transaction(
        user_id="user-001",
        date=dt.datetime.strptime("2025-08-04", "%Y-%m-%d"),
        account_id="acct-001",
        vendor="Grocery Store",
        amount=42.50,
        category=TransactionCategory.GROCERIES,
        reviewed=False,
    )

    transactions_table.put_transaction(new_txn)

    # Verify it can be retrieved
    fetched = transactions_table.get_transaction(
        user_id=new_txn.user_id,
        date=new_txn.date,
        transaction_id=new_txn.transaction_id,
    )
    assert isinstance(fetched, Transaction)
    assert fetched.vendor == "Grocery Store"
    assert fetched.amount == pytest.approx(42.50)
    assert fetched.category == TransactionCategory.GROCERIES

    # Delete and verify removal
    transactions_table.delete_transaction(
        user_id=new_txn.user_id,
        date=new_txn.date,
        transaction_id=new_txn.transaction_id,
    )
    assert (
        transactions_table.get_transaction(
            user_id=new_txn.user_id,
            date=new_txn.date,
            transaction_id=new_txn.transaction_id,
        )
        is None
    )
