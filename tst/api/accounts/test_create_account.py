import json

import pytest

from src.api.accounts.create_account import CreateAccount
from src.api.common.models import HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.database.client import WalterDB
from src.metrics.client import DatadogMetricsClient


@pytest.fixture
def create_account_api(
    walter_authenticator: WalterAuthenticator,
    datadog_metrics: DatadogMetricsClient,
    walter_db: WalterDB,
) -> CreateAccount:
    return CreateAccount(walter_authenticator, datadog_metrics, walter_db)


def _event_with_auth_and_body(token: str, body: dict) -> dict:
    return {
        "path": "/accounts",
        "httpMethod": "POST",
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
    user_id = "user-001"
    session_id = "session-001"
    token, token_expiry = walter_authenticator.generate_access_token(
        user_id, session_id
    )
    user = walter_db.get_user_by_email(email)
    event = _event_with_auth_and_body(
        token,
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
    create_account_api: CreateAccount, walter_authenticator: WalterAuthenticator
) -> None:
    user_id = "user-001"
    session_id = "session-001"
    token, token_expiry = walter_authenticator.generate_access_token(
        user_id, session_id
    )
    # omit account_type
    event = _event_with_auth_and_body(
        token,
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
    assert response.http_status == HTTPStatus.BAD_REQUEST
    assert response.status == Status.SUCCESS
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
    assert response.http_status == HTTPStatus.UNAUTHORIZED
    assert response.status == Status.SUCCESS
    assert response.message == "Not authenticated! Token is expired or invalid."


def test_create_account_failure_session_does_not_exist(
    create_account_api: CreateAccount, walter_authenticator: WalterAuthenticator
) -> None:
    user_id = "user-001"
    session_id = "session-does-not-exist"
    token, token_expiry = walter_authenticator.generate_access_token(
        user_id, session_id
    )
    event = _event_with_auth_and_body(
        token,
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
    assert response.http_status == HTTPStatus.UNAUTHORIZED
    assert response.status == Status.SUCCESS
    assert response.message == "Not authenticated! Session does not exist."
