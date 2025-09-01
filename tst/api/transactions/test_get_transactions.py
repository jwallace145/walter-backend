import pytest

from src.api.common.models import HTTPStatus, Status
from src.api.transactions.get_transactions.method import GetTransactions
from src.auth.authenticator import WalterAuthenticator
from src.database.client import WalterDB
from src.metrics.client import DatadogMetricsClient


@pytest.fixture()
def get_transactions_api(
    walter_authenticator: WalterAuthenticator,
    datadog_metrics: DatadogMetricsClient,
    walter_db: WalterDB,
):
    return GetTransactions(walter_authenticator, datadog_metrics, walter_db)


def create_get_transactions_event(token: str, query: dict) -> dict:
    return {
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
    get_transactions_api: GetTransactions, walter_authenticator: WalterAuthenticator
):
    user = "user-002"
    session = "session-004"
    token, token_expiry = walter_authenticator.generate_access_token(user, session)
    event = create_get_transactions_event(
        token=token,
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
    get_transactions_api: GetTransactions, walter_authenticator: WalterAuthenticator
):
    user_id = "user-002"
    session_id = "session-004"
    token, token_expiry = walter_authenticator.generate_access_token(
        user_id, session_id
    )
    # acct-003 has 3 banking transactions in the seed
    event = create_get_transactions_event(
        token=token,
        query={
            "start_date": "2025-08-01",
            "end_date": "2025-08-08",
            "account_id": "acct-003",
        },
    )
    response = get_transactions_api.invoke(event)

    assert response.http_status == HTTPStatus.OK
    assert response.status == Status.SUCCESS
    assert response.data is not None

    data = response.data
    assert data["num_transactions"] == 3

    # Validate all returned transactions belong to acct-003 and expected IDs are included
    txn_accounts = {t["account_id"] for t in data["transactions"]}
    assert txn_accounts == {"acct-003"}

    txn_ids = {t["transaction_id"] for t in data["transactions"]}
    assert {
        "bank-txn-001",
        "bank-txn-002",
        "bank-txn-003",
    } == txn_ids
    assert response.data["total_income"] == pytest.approx(2500.00)
    assert response.data["total_expense"] == pytest.approx(1505.00)
    assert response.data["cash_flow"] == pytest.approx(995.00)


def test_get_account_transactions_date_filter_single_day(
    get_transactions_api: GetTransactions, walter_authenticator: WalterAuthenticator
):
    user_id = "user-002"
    session_id = "session-004"
    token, token_expiry = walter_authenticator.generate_access_token(
        user_id, session_id
    )
    # On 2025-08-06 there are two banking transactions for acct-003
    event = create_get_transactions_event(
        token=token,
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


def test_get_account_transactions_failure_account_does_not_exist(
    get_transactions_api: GetTransactions, walter_authenticator: WalterAuthenticator
) -> None:
    user_id = "user-001"
    session_id = "session-001"
    token, token_expiry = walter_authenticator.generate_access_token(
        user_id, session_id
    )
    event = create_get_transactions_event(
        token=token,
        query={
            "start_date": "2025-08-01",
            "end_date": "2025-08-31",
            "account_id": "acct-004",
        },
    )
    response = get_transactions_api.invoke(event)
    assert response.http_status == HTTPStatus.NOT_FOUND
    assert response.status == Status.FAILURE
    assert "Account does not exist" in response.message
