import json
from datetime import datetime

import pytest

from src.api.transactions.delete_transaction import DeleteTransaction
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB


@pytest.fixture
def delete_transaction_api(
    walter_authenticator: WalterAuthenticator,
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
) -> DeleteTransaction:
    return DeleteTransaction(walter_authenticator, walter_cw, walter_db)


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


def test_delete_buy_investment_transaction(
    delete_transaction_api: DeleteTransaction,
    walter_db: WalterDB,
    walter_authenticator: WalterAuthenticator,
) -> None:
    # create test delete transaction event, user has a holding for this security
    email = "lucy@gmail.com"
    jwt = walter_authenticator.generate_user_token(email)
    event = create_delete_transaction_event(jwt, "investment-txn-007", "2025-08-01")

    # assert holding exists prior to api invocation
    holding = walter_db.get_holding("acct-007", "sec-nasdaq-aapl")
    assert holding is not None
    assert holding.quantity == pytest.approx(2.0)
    assert holding.average_cost_basis == pytest.approx(75.0)
    assert holding.total_cost_basis == pytest.approx(150.0)

    # invoke delete transaction api
    delete_transaction_api.invoke(event)

    # assert holding was deleted successfully
    holding = walter_db.get_holding("acct-007", "sec-nasdaq-aapl")
    assert holding is None

    # assert transaction was deleted successfully
    transaction = walter_db.get_transaction(
        "acct-007", "investment-txn-007", datetime.strptime("2025-08-01", "%Y-%m-%d")
    )
    assert transaction is None


# def test_delete_sell_investment_transaction(
#     delete_transaction_api: DeleteTransaction,
#     walter_db: WalterDB,
#     walter_authenticator: WalterAuthenticator,
# ) -> None:
#     pass
