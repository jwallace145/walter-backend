import pytest

from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Status
from src.api.factory import APIMethod, APIMethodFactory
from src.api.routing.methods import HTTPMethod
from src.api.transactions.delete_transaction import DeleteTransaction
from src.auth.authenticator import WalterAuthenticator
from src.database.client import WalterDB
from src.database.transactions.models import InvestmentTransaction
from tst.api.utils import UNIT_TEST_REQUEST_ID, get_api_event

DELETE_TRANSACTION_API_PATH = "/transactions"
"""(str): Path to the delete transaction API endpoint."""

DELETE_TRANSACTION_API_METHOD = HTTPMethod.DELETE
"""(HTTPMethod): HTTP method for the delete transaction API endpoint."""


@pytest.fixture
def delete_transaction_api(
    api_method_factory: APIMethodFactory,
) -> WalterAPIMethod:
    return api_method_factory.get_api(
        APIMethod.DELETE_TRANSACTION, UNIT_TEST_REQUEST_ID
    )


def test_delete_buy_investment_transaction_failure_invalid_holding_update(
    delete_transaction_api: DeleteTransaction,
    walter_db: WalterDB,
    walter_authenticator: WalterAuthenticator,
) -> None:
    # create test delete transaction event, user has a holding for this security
    user_id = "user-005"
    session_id = "session-005"
    account_id = "acct-007"
    transaction_id = "investment-txn-010"
    security_id = "sec-nyse-coke"
    token, token_expiry = walter_authenticator.generate_access_token(
        user_id, session_id
    )
    event = get_api_event(
        DELETE_TRANSACTION_API_PATH,
        DELETE_TRANSACTION_API_METHOD,
        token=token,
        query={"transaction_id": transaction_id},
    )

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
    transaction = walter_db.get_user_transaction(user_id, transaction_id)
    assert transaction is not None
    assert transaction.transaction_id == transaction_id
    assert isinstance(transaction, InvestmentTransaction)
    assert transaction.security_id == security_id
