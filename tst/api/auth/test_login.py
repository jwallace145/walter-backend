import pytest

from src.api.auth.login.method import Login
from src.api.common.models import HTTPStatus, Status
from src.api.routing.methods import HTTPMethod
from src.auth.authenticator import WalterAuthenticator
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.database.users.models import User
from src.environment import Domain
from src.metrics.client import DatadogMetricsClient
from tst.api.utils import get_api_event, get_expected_response

LOGIN_API_PATH = "/auth/login"
"""(str): Path to the login API endpoint."""

LOGIN_API_METHOD = HTTPMethod.POST
"""(HTTPMethod): HTTP method for the login API endpoint."""


@pytest.fixture
def login_api(
    walter_authenticator: WalterAuthenticator,
    datadog_metrics: DatadogMetricsClient,
    walter_db: WalterDB,
    walter_sm: WalterSecretsManagerClient,
) -> Login:
    return Login(
        Domain.TESTING, walter_authenticator, datadog_metrics, walter_db, walter_sm
    )


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

    event = get_api_event(
        LOGIN_API_PATH,
        LOGIN_API_METHOD,
        body={"email": email, "password": password},
    )

    response = login_api.invoke(event)

    assert response.http_status == HTTPStatus.OK
    assert response.status == Status.SUCCESS
    assert response.message == "User logged in successfully!"
    assert "access_token" in response.data
    assert "refresh_token" in response.data
    assert "access_token_expires_at" in response.data
    assert "refresh_token_expires_at" in response.data
    assert response.data["user_id"] == walter_db.get_user_by_email(email).user_id


def test_login_failure_user_does_not_exist(login_api: Login) -> None:
    event = get_api_event(
        LOGIN_API_PATH,
        LOGIN_API_METHOD,
        body={"email": "nouser@example.com", "password": "pw"},
    )

    expected_response = get_expected_response(
        api_name=login_api.API_NAME,
        status_code=HTTPStatus.NOT_FOUND,
        status=Status.SUCCESS,
        message="User with email 'nouser@example.com' does not exist!",
    )

    assert expected_response == login_api.invoke(event)


def test_login_failure_invalid_email_format(login_api: Login) -> None:
    event = get_api_event(
        LOGIN_API_PATH,
        LOGIN_API_METHOD,
        body={"email": "invalid-email", "password": "pw"},
    )

    expected_response = get_expected_response(
        api_name=login_api.API_NAME,
        status_code=HTTPStatus.UNAUTHORIZED,
        status=Status.SUCCESS,
        message="Invalid email!",
    )

    assert expected_response == login_api.invoke(event)


def test_login_failure_incorrect_password(
    login_api: Login, walter_db: WalterDB, walter_authenticator: WalterAuthenticator
) -> None:
    email = "someone@example.com"
    real_password = "CorrectHorseBatteryStaple"
    _, password_hash = walter_authenticator.hash_secret(real_password)

    user = User(
        user_id=None,
        email=email,
        first_name="Some",
        last_name="One",
        password_hash=password_hash.decode(),
    )
    walter_db.users_table.create_user(user)

    event = get_api_event(
        LOGIN_API_PATH,
        LOGIN_API_METHOD,
        body={"email": email, "password": "wrong"},
    )

    expected_response = get_expected_response(
        api_name=login_api.API_NAME,
        status_code=HTTPStatus.UNAUTHORIZED,
        status=Status.SUCCESS,
        message="Password incorrect!",
    )

    assert expected_response == login_api.invoke(event)
