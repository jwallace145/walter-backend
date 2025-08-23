import json

import pytest

from src.api.auth.login.method import Login
from src.api.common.models import HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.database.users.models import User
from tst.api.utils import get_expected_response


@pytest.fixture
def login_api(
    walter_authenticator: WalterAuthenticator,
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
    walter_sm: WalterSecretsManagerClient,
) -> Login:
    return Login(walter_authenticator, walter_cw, walter_db, walter_sm)


def _event_with_body(body: dict) -> dict:
    return {
        "headers": {
            "content-type": "application/json",
            "User-Agent": "pytest/1.0",
        },
        "queryStringParameters": None,
        "body": json.dumps(body) if not isinstance(body, str) else body,
        "requestContext": {
            "identity": {
                "sourceIp": "127.0.0.1",
            }
        },
    }


def test_login_success(
    login_api: Login,
    walter_db: WalterDB,
    walter_authenticator: WalterAuthenticator,
) -> None:
    # Arrange: create a user with a properly hashed password
    email = "newuser@example.com"
    password = "StrongPassword!123"
    _, password_hash = walter_authenticator.hash_secret(password)

    user = User(
        user_id="new-user",
        email=email,
        first_name="New",
        last_name="User",
        password_hash=password_hash.decode(),
    )
    walter_db.users_table.create_user(user)

    event = _event_with_body({"email": email, "password": password})

    # Act
    response = login_api.invoke(event)

    # Assert
    assert response.http_status == HTTPStatus.OK
    assert response.status == Status.SUCCESS
    assert response.message == "User logged in successfully!"
    assert "access_token" in response.data
    assert "refresh_token" in response.data
    assert "access_token_expires_at" in response.data
    assert "refresh_token_expires_at" in response.data
    assert response.data["user_id"] == walter_db.get_user_by_email(email).user_id


def test_login_failure_user_does_not_exist(login_api: Login) -> None:
    event = _event_with_body({"email": "nouser@example.com", "password": "pw"})

    expected_response = get_expected_response(
        api_name=login_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="User with email 'nouser@example.com' does not exist!",
    )

    assert expected_response == login_api.invoke(event)


def test_login_failure_invalid_email_format(login_api: Login) -> None:
    # invalid email should be caught by validate_fields
    event = _event_with_body({"email": "invalid-email", "password": "pw"})

    expected_response = get_expected_response(
        api_name=login_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Invalid email!",
    )

    assert expected_response == login_api.invoke(event)


def test_login_failure_incorrect_password(
    login_api: Login, walter_db: WalterDB, walter_authenticator: WalterAuthenticator
) -> None:
    # Arrange - create user with a known password
    email = "someone@example.com"
    real_password = "CorrectHorseBatteryStaple"
    _, password_hash = walter_authenticator.hash_secret(real_password)

    from src.database.users.models import User

    user = User(
        user_id=None,
        email=email,
        first_name="Some",
        last_name="One",
        password_hash=password_hash.decode(),
    )
    walter_db.users_table.create_user(user)

    # Act - wrong password
    event = _event_with_body({"email": email, "password": "wrong"})

    expected_response = get_expected_response(
        api_name=login_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Password incorrect!",
    )

    # Assert
    assert expected_response == login_api.invoke(event)
