import pytest

from src.api.auth_user import AuthUser
from src.api.methods import Status, HTTPStatus
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from tst.api.utils import get_auth_user_event, get_expected_response


@pytest.fixture
def auth_user_api(
    walter_authenticator: WalterAuthenticator,
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
    walter_sm: WalterSecretsManagerClient,
) -> AuthUser:
    return AuthUser(walter_authenticator, walter_cw, walter_db, walter_sm)


def test_auth_user_failure_invalid_email(auth_user_api: AuthUser) -> None:
    event = get_auth_user_event(email="walter", password="walter")
    expected_response = get_expected_response(
        api_name=auth_user_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Invalid email!",
    )
    assert expected_response == auth_user_api.invoke(event)


def test_auth_user_failure_user_does_not_exist(auth_user_api: AuthUser) -> None:
    event = get_auth_user_event(email="sally@gmail.com", password="sally")
    expected_response = get_expected_response(
        api_name=auth_user_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="User not found!",
    )
    assert expected_response == auth_user_api.invoke(event)
