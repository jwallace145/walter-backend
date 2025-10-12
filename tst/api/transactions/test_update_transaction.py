import pytest

from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Status
from src.api.factory import APIMethod, APIMethodFactory
from src.api.routing.methods import HTTPMethod
from src.api.transactions.edit_transaction import EditTransaction
from src.auth.authenticator import WalterAuthenticator
from tst.api.utils import UNIT_TEST_REQUEST_ID, get_api_event


@pytest.fixture()
def update_transaction_api(
    api_method_factory: APIMethodFactory,
) -> WalterAPIMethod:
    return api_method_factory.get_api(APIMethod.EDIT_TRANSACTION, UNIT_TEST_REQUEST_ID)


UPDATE_TRANSACTION_API_PATH = "/transactions"
UPDATE_TRANSACTION_API_METHOD = HTTPMethod.PUT


def test_update_transaction_success(
    update_transaction_api: EditTransaction, walter_authenticator: WalterAuthenticator
) -> None:
    user = "user-001"
    session = "session-001"
    token, token_expiry = walter_authenticator.generate_access_token(user, session)
    event = get_api_event(
        UPDATE_TRANSACTION_API_PATH,
        UPDATE_TRANSACTION_API_METHOD,
        token=token,
        body={
            "transaction_date": "2025-08-01",
            "transaction_id": "bank-txn-006",
            "updated_merchant_name": "updated merchant name",
            "updated_category": "Restaurants",
        },
    )
    response = update_transaction_api.invoke(event)
    assert response.http_status == HTTPStatus.OK
    assert response.status == Status.SUCCESS
    assert response.data is not None

    data = response.data
    assert data["transaction"]["transaction_id"] == "bank-txn-006"
    assert data["transaction"]["merchant_name"] == "updated merchant name"
    assert data["transaction"]["transaction_category"] == "Restaurants"


def test_update_transaction_failure_transaction_does_not_exist(
    update_transaction_api: EditTransaction, walter_authenticator: WalterAuthenticator
) -> None:
    user = "user-001"
    session = "session-001"
    token, token_expiry = walter_authenticator.generate_access_token(user, session)
    event = get_api_event(
        UPDATE_TRANSACTION_API_PATH,
        UPDATE_TRANSACTION_API_METHOD,
        token=token,
        body={
            "transaction_date": "2025-08-01",
            "transaction_id": "non-existent-txn",
            "updated_merchant_name": "updated merchant name",
            "updated_category": "Restaurants",
        },
    )
    response = update_transaction_api.invoke(event)
    assert response.http_status == HTTPStatus.NOT_FOUND
    assert response.status == Status.SUCCESS
    assert "does not exist" in response.message


def test_update_transaction_failure_invalid_transaction_category(
    update_transaction_api: EditTransaction, walter_authenticator: WalterAuthenticator
) -> None:
    user = "user-001"
    session = "session-001"
    token, token_expiry = walter_authenticator.generate_access_token(user, session)
    event = get_api_event(
        UPDATE_TRANSACTION_API_PATH,
        UPDATE_TRANSACTION_API_METHOD,
        token=token,
        body={
            "transaction_date": "2025-08-01",
            "transaction_id": "bank-txn-006",
            "updated_merchant_name": "updated merchant name",
            "updated_category": "InvalidCategory",  # Using an invalid category
        },
    )
    response = update_transaction_api.invoke(event)
    assert response.http_status == HTTPStatus.BAD_REQUEST
    assert response.status == Status.SUCCESS
    assert "Invalid transaction category" in response.message
