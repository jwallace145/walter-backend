import datetime as dt

import pytest

from src.ai.mlp.expenses import ExpenseCategorizerMLP
from src.database.client import WalterDB
from src.database.transactions.models import BankTransaction
from src.plaid.transaction_converter import TransactionConverter
from tst.plaid.utils import create_plaid_transaction


@pytest.fixture
def transaction_converter(
    walter_db: WalterDB, transactions_categorizer: ExpenseCategorizerMLP
) -> TransactionConverter:
    return TransactionConverter(walter_db, transactions_categorizer)


def test_transaction_converter(transaction_converter: TransactionConverter) -> None:
    plaid_account_id = "plaid-acct-001"
    plaid_transaction_id = "plaid-txn-001"
    account_id = "acct-001"
    merchant_name = "Uber"
    amount = 6.33
    date = dt.datetime(2025, 8, 30)
    plaid_transaction = create_plaid_transaction(
        plaid_account_id, plaid_transaction_id, merchant_name, amount, date
    )
    transaction = transaction_converter.convert(plaid_transaction)

    assert isinstance(transaction, BankTransaction)
    assert transaction.plaid_account_id == plaid_account_id
    assert transaction.plaid_transaction_id == plaid_transaction_id
    assert transaction.account_id == account_id
    assert transaction.merchant_name == merchant_name
    assert transaction.transaction_amount == amount
    assert transaction.get_transaction_date() == date
