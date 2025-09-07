import pytest

from src.api.common.methods import HTTPStatus, Status
from src.api.routing.methods import HTTPMethod
from src.api.users.create_user import CreateUser
from src.auth.authenticator import WalterAuthenticator
from src.aws.ses.client import WalterSESClient
from src.database.client import WalterDB
from src.environment import Domain
from src.metrics.client import DatadogMetricsClient
from tst.api.utils import get_api_event, get_expected_response

CREATE_USER_API_PATH = "/users"
"""(str): Path to the create user API endpoint."""

CREATE_USER_API_METHOD = HTTPMethod.POST
"""(HTTPMethod): HTTP method for the create user API endpoint."""


@pytest.fixture
def create_user_api(
    walter_authenticator: WalterAuthenticator,
    datadog_metrics: DatadogMetricsClient,
    walter_db: WalterDB,
    walter_ses: WalterSESClient,
) -> CreateUser:
    return CreateUser(Domain.TESTING, walter_authenticator, datadog_metrics, walter_db)


# def test_create_user(create_user_api: CreateUser) -> None:
#     event = get_create_user_event(
#         email="jim@gmail.com", username="jim", password="Test1234"
#     )
#     expected_response = get_expected_response(
#         api_name=create_user_api.API_NAME,
#         status_code=HTTPStatus.CREATED,
#         status=Status.SUCCESS,
#         message="User created!",
#     )
#     assert expected_response == create_user_api.invoke(event)


# def test_create_user_success_uppercase_email_stored_as_lowercase(
#     create_user_api: CreateUser, walter_db: WalterDB
# ) -> None:
#     event = get_create_user_event(
#         email="JIMMY@gmail.com", username="jimmy", password="Test1234"
#     )
#     expected_response = get_expected_response(
#         api_name=create_user_api.API_NAME,
#         status_code=HTTPStatus.CREATED,
#         status=Status.SUCCESS,
#         message="User created!",
#     )
#     assert expected_response == create_user_api.invoke(event)
#     user = walter_db.get_user("jimmy@gmail.com")
#     assert user.email == "jimmy@gmail.com"


def test_create_user_failure_invalid_email(create_user_api: CreateUser) -> None:
    event = get_api_event(
        CREATE_USER_API_PATH,
        CREATE_USER_API_METHOD,
        token=None,
        body={
            "email": "invalid-email",
            "first_name": "Jimmy",
            "last_name": "Smith",
            "password": "Test1234",
        },
    )
    expected_response = get_expected_response(
        api_name=create_user_api.API_NAME,
        status_code=HTTPStatus.BAD_REQUEST,
        status=Status.SUCCESS,
        message="Invalid email!",
    )
    assert expected_response == create_user_api.invoke(event)


def test_create_user_failure_user_already_exists(create_user_api: CreateUser) -> None:
    event = get_api_event(
        CREATE_USER_API_PATH,
        CREATE_USER_API_METHOD,
        token=None,
        body={
            "email": "walter@gmail.com",
            "first_name": "Walter",
            "last_name": "Walrus",
            "password": "Test1234",
        },
    )
    expected_response = get_expected_response(
        api_name=create_user_api.API_NAME,
        status_code=HTTPStatus.CONFLICT,
        status=Status.SUCCESS,
        message="User already exists!",
    )
    assert expected_response == create_user_api.invoke(event)


def test_create_user_failure_invalid_password(create_user_api: CreateUser) -> None:
    event = get_api_event(
        CREATE_USER_API_PATH,
        CREATE_USER_API_METHOD,
        token=None,
        body={
            "email": "jim@gmail.com",
            "first_name": "Jimmy",
            "last_name": "Smith",
            "password": "test",
        },
    )
    expected_response = get_expected_response(
        api_name=create_user_api.API_NAME,
        status_code=HTTPStatus.BAD_REQUEST,
        status=Status.SUCCESS,
        message="Password is invalid! Must be at least 8 characters long and include 3/4 of the following: uppercase letters, lowercase letters, numbers, and special characters.",
    )
    assert expected_response == create_user_api.invoke(event)
