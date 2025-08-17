import datetime as dt

import pytest

from src.database.client import WalterDB
from src.database.transactions.models import (
    InvestmentTransaction,
)
from src.investments.holdings.exceptions import InvalidHoldingUpdate
from src.investments.holdings.updater import HoldingUpdater


def test_update_holding_invalid_transactions(
    holding_updater: HoldingUpdater, walter_db: WalterDB
) -> None:
    """
    This unit test ensures that the holding updater does not update a holding if the
    transactions are invalid.

    For example, this scenario can occur when a user buys a security multiple times and
    then sells a portion of the owned shares. Then, if the user attempts to delete a buy
    transaction that results in a subsequent invalid sell transaction, the holding should
    not be updated to preserve the security transaction history validity.
    """
    account_id = "acct-007"
    transaction_id = "investment-txn-010"
    transaction_date = "2025-08-02"
    security_id = "sec-nyse-coke"

    transaction = walter_db.get_transaction(
        account_id, transaction_id, dt.datetime.strptime(transaction_date, "%Y-%m-%d")
    )

    # assert transaction exists prior to testing delete holding update
    assert transaction is not None
    assert transaction.transaction_id == transaction_id
    assert isinstance(transaction, InvestmentTransaction)
    assert transaction.security_id == security_id

    # assert an exception is raised for an invalid holding update
    with pytest.raises(InvalidHoldingUpdate):
        holding_updater.delete_transaction(transaction)
