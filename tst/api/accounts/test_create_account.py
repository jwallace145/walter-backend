import json

import pytest

from src.api.accounts.create_account import CreateAccount
from src.api.common.models import HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB


@pytest.fixture
def create_account_api(
    walter_authenticator: WalterAuthenticator,
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
) -> CreateAccount:
    return CreateAccount(walter_authenticator, walter_cw, walter_db)


def _event_with_auth_and_body(token: str, body: dict) -> dict:
    return {
        "headers": {"Authorization": f"Bearer {token}"},
        "queryStringParameters": None,
        "body": json.dumps(body),
    }


def test_create_account_success(
    create_account_api: CreateAccount,
    walter_db: WalterDB,
    walter_authenticator: WalterAuthenticator,
) -> None:
    email = "walter@gmail.com"
    jwt = walter_authenticator.generate_user_token(email)
    user = walter_db.get_user_by_email("walter@gmail.com")
    event = _event_with_auth_and_body(
        jwt,
        {
            "account_type": "credit",
            "account_subtype": "credit card",
            "institution_name": "Capital One",
            "account_name": "Venture X",
            "account_mask": "1234",
            "balance": 123.45,
        },
    )

    response = create_account_api.invoke(event)

    assert response.http_status == HTTPStatus.CREATED
    assert response.status == Status.SUCCESS
    assert response.message == "Account created successfully!"
    assert response.data is not None and "account" in response.data

    created = response.data["account"]
    assert created["user_id"] == user.user_id
    assert created["account_type"] == "credit"
    assert created["account_subtype"] == "credit card"
    assert created["institution_name"] == "Capital One"
    assert created["account_name"] == "Venture X"
    assert created["account_mask"] == "1234"
    assert created["balance"] == 123.45


def test_create_account_failure_missing_required_field(
    create_account_api: CreateAccount, jwt_walter: str
) -> None:
    # omit account_type
    event = _event_with_auth_and_body(
        jwt_walter,
        {
            "account_subtype": "credit card",
            "institution_name": "Capital One",
            "account_name": "Venture X",
            "account_mask": "1234",
            "balance": 100.0,
        },
    )
    # Base class returns BadRequest as handled exception => HTTPStatus.OK, Failure
    expected_message = "Client bad request! Missing required field: 'account_type'"
    response = create_account_api.invoke(event)
    assert response.http_status == HTTPStatus.OK
    assert response.status == Status.FAILURE
    assert response.message == expected_message


def test_create_account_failure_not_authenticated(
    create_account_api: CreateAccount,
) -> None:
    event = _event_with_auth_and_body(
        "invalid-token",
        {
            "account_type": "credit",
            "account_subtype": "credit card",
            "institution_name": "Capital One",
            "account_name": "Venture X",
            "account_mask": "1234",
            "balance": 10.0,
        },
    )
    response = create_account_api.invoke(event)
    assert response.http_status == HTTPStatus.OK
    assert response.status == Status.FAILURE
    assert response.message == "Not authenticated! Token is invalid."


def test_create_account_failure_user_does_not_exist(
    create_account_api: CreateAccount, walter_authenticator: WalterAuthenticator
) -> None:
    ghost_token = walter_authenticator.generate_user_token("ghost@ghost.com")
    event = _event_with_auth_and_body(
        ghost_token,
        {
            "account_type": "depository",
            "account_subtype": "checking",
            "institution_name": "Chase",
            "account_name": "Checking",
            "account_mask": "0000",
            "balance": 0.0,
        },
    )
    response = create_account_api.invoke(event)
    assert response.http_status == HTTPStatus.OK
    assert response.status == Status.FAILURE
    assert response.message == "User with email 'ghost@ghost.com' does not exist!"
