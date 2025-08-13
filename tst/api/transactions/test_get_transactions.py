import pytest

from src.api.common.models import Status, HTTPStatus
from src.api.transactions.get_transactions import GetTransactions
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB


@pytest.fixture()
def get_transactions_api(
    walter_authenticator: WalterAuthenticator,
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
):
    return GetTransactions(walter_authenticator, walter_cw, walter_db)


def create_get_transactions_event(token: str, query: dict) -> dict:
    return {
        "resource": "/transactions",
        "path": "/transactions",
        "httpMethod": "GET",
        "headers": {
            "Authorization": f"Bearer {token}",
            "content-type": "application/json",
        },
        "queryStringParameters": query,
        "body": None,
    }


def test_get_account_transactions_acct003_full_range_success(
    get_transactions_api: GetTransactions, jwt_walrus: str
):
    # acct-003 has 3 banking transactions across Aug 2025
    event = create_get_transactions_event(
        token=jwt_walrus,
        query={
            "start_date": "2025-08-01",
            "end_date": "2025-08-31",
            "account_id": "acct-003",
        },
    )
    response = get_transactions_api.invoke(event)

    assert response.http_status == HTTPStatus.OK
    assert response.status == Status.SUCCESS
    assert response.data is not None

    data = response.data
    assert data["num_transactions"] == 3

    # Ensure known transaction ids are present
    txn_ids = {t["transaction_id"] for t in data["transactions"]}
    assert {"bank-txn-001", "bank-txn-002", "bank-txn-003"} == txn_ids

    # Sanity check aggregation fields exist
    assert "total_income" in data
    assert "total_expense" in data
    assert "cash_flow" in data


def test_get_account_transactions_success(
    get_transactions_api: GetTransactions, jwt_walrus: str
):
    # acct-002 has 4 investment transactions in the seed
    event = create_get_transactions_event(
        token=jwt_walrus,
        query={
            "start_date": "2025-08-01",
            "end_date": "2025-08-08",
            "account_id": "acct-002",
        },
    )
    response = get_transactions_api.invoke(event)

    assert response.http_status == HTTPStatus.OK
    assert response.status == Status.SUCCESS
    assert response.data is not None

    data = response.data
    assert data["num_transactions"] == 4

    # Validate all returned transactions belong to acct-002 and expected IDs are included
    txn_accounts = {t["account_id"] for t in data["transactions"]}
    assert txn_accounts == {"acct-002"}

    txn_ids = {t["transaction_id"] for t in data["transactions"]}
    assert {
        "investment-txn-001",
        "investment-txn-002",
        "investment-txn-003",
        "investment-txn-004",
    } == txn_ids


def test_get_account_transactions_date_filter_single_day(
    get_transactions_api: GetTransactions, jwt_walrus: str
):
    # On 2025-08-06 there are two banking transactions for acct-003
    event = create_get_transactions_event(
        token=jwt_walrus,
        query={
            "start_date": "2025-08-06",
            "end_date": "2025-08-06",
            "account_id": "acct-003",
        },
    )
    response = get_transactions_api.invoke(event)

    assert response.http_status == HTTPStatus.OK
    assert response.status == Status.SUCCESS
    assert response.data is not None

    data = response.data
    assert data["num_transactions"] == 2

    txn_ids = {t["transaction_id"] for t in data["transactions"]}
    assert {"bank-txn-002", "bank-txn-003"} == txn_ids
