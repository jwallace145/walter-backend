import json
from datetime import datetime

import pytest

from src.api.common.models import HTTPStatus, Status
from src.api.transactions.delete_transaction import DeleteTransaction
from src.auth.authenticator import WalterAuthenticator
from src.database.client import WalterDB
from src.database.transactions.models import InvestmentTransaction
from src.investments.holdings.updater import HoldingUpdater
from src.metrics.client import DatadogMetricsClient


@pytest.fixture
def delete_transaction_api(
    walter_authenticator: WalterAuthenticator,
    datadog_metrics: DatadogMetricsClient,
    walter_db: WalterDB,
    holding_updater: HoldingUpdater,
) -> DeleteTransaction:
    return DeleteTransaction(
        walter_authenticator, datadog_metrics, walter_db, holding_updater
    )


def create_delete_transaction_event(
    token: str, transaction_id: str, transaction_date: str
) -> dict:
    return {
        "path": "/transactions",
        "httpMethod": "DELETE",
        "headers": {
            "Authorization": f"Bearer {token}",
            "content-type": "application/json",
        },
        "queryStringParameters": None,
        "pathParameters": {},
        "body": json.dumps(
            {
                "date": transaction_date,
                "transaction_id": transaction_id,
            }
        ),
    }


def test_delete_buy_investment_transaction_failure_invalid_holding_update(
    delete_transaction_api: DeleteTransaction,
    walter_db: WalterDB,
    walter_authenticator: WalterAuthenticator,
) -> None:
    # create test delete transaction event, user has a holding for this security
    user_id = "user-005"
    session_id = "session-005"
    account_id = "acct-007"
    transaction_date = "2025-08-02"
    transaction_id = "investment-txn-010"
    security_id = "sec-nyse-coke"
    token, token_expiry = walter_authenticator.generate_access_token(
        user_id, session_id
    )
    event = create_delete_transaction_event(token, transaction_id, transaction_date)

    # assert holding exists prior to api invocation
    holding = walter_db.get_holding(account_id, security_id)
    assert holding is not None
    assert holding.quantity == pytest.approx(20.0)
    assert holding.average_cost_basis == pytest.approx(150.0)
    assert holding.total_cost_basis == pytest.approx(3000.0)

    # invoke delete transaction api
    response = delete_transaction_api.invoke(event)

    # assert response details
    assert response.http_status == HTTPStatus.BAD_REQUEST
    assert response.status == Status.SUCCESS
    assert "greater than holding quantity" in response.message

    # assert holding was not updated
    holding = walter_db.get_holding(account_id, security_id)
    assert holding is not None
    assert holding.quantity == pytest.approx(20.0)
    assert holding.average_cost_basis == pytest.approx(150.0)
    assert holding.total_cost_basis == pytest.approx(3000.0)

    # assert transaction still exists
    transaction = walter_db.get_transaction(
        account_id, transaction_id, datetime.strptime(transaction_date, "%Y-%m-%d")
    )
    assert transaction is not None
    assert transaction.transaction_id == transaction_id
    assert isinstance(transaction, InvestmentTransaction)
    assert transaction.security_id == security_id
