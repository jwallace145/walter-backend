import datetime as dt

import pytest

from src.ai.mlp.expenses import ExpenseCategorizerMLP
from src.api.common.models import HTTPStatus, Status
from src.api.transactions.add_transaction import AddTransaction
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from tst.api.utils import get_add_transaction_event, get_expected_response


@pytest.fixture
def add_transaction_api(
    walter_authenticator: WalterAuthenticator,
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
    transactions_categorizer: ExpenseCategorizerMLP,
) -> AddTransaction:
    return AddTransaction(
        walter_authenticator, walter_cw, walter_db, transactions_categorizer
    )


def test_add_transaction(
    add_transaction_api: AddTransaction, jwt_walter: str, walter_db: WalterDB
) -> None:
    # verify user transaction does not exist before adding the transaction
    transactions = walter_db.get_transactions(
        user_id="f47ac10b-58cc-4372-a567-0e02b2c3d479",
        start_date=dt.datetime.strptime("2025-07-31", "%Y-%m-%d"),
        end_date=dt.datetime.strptime("2025-08-02", "%Y-%m-%d"),
    )
    assert len(transactions) == 0
    # create add transaction event with required details
    event = get_add_transaction_event(
        token=jwt_walter,
        account_id="5oqvleLkpZt1l1lpKGd9fB8xEymDxaF9bA45z",
        date="2025-08-01",
        vendor="Starbucks",
        amount=5.00,
    )
    # add the user transaction via the api
    add_transaction_api.invoke(event)
    transactions = walter_db.get_transactions(
        user_id="f47ac10b-58cc-4372-a567-0e02b2c3d479",
        start_date=dt.datetime.strptime("2025-07-31", "%Y-%m-%d"),
        end_date=dt.datetime.strptime("2025-08-02", "%Y-%m-%d"),
    )
    assert len(transactions) == 1
    assert transactions[0].transaction.vendor == "Starbucks"
    assert transactions[0].transaction.amount == 5.00


def test_add_transaction_failure_cash_account_does_not_exist(
    add_transaction_api: AddTransaction, jwt_walter: str, walter_db: WalterDB
) -> None:
    # create add transaction event with an invalid cash account
    event = get_add_transaction_event(
        token=jwt_walter,
        account_id="INVALID_ACCOUNT_ID",
        date="2025-08-01",
        vendor="Starbucks",
        amount=5.00,
    )
    expected_response = get_expected_response(
        api_name=add_transaction_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Account does not exist for user!",
    )
    assert expected_response == add_transaction_api.invoke(event)
