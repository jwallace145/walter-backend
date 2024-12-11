import pytest

from src.api.change_password import ChangePassword
from src.api.common.models import HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from tst.api.utils import get_change_password_event, get_expected_response


@pytest.fixture
def change_password_api(
    walter_authenticator: WalterAuthenticator,
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
) -> ChangePassword:
    return ChangePassword(walter_authenticator, walter_cw, walter_db)


def test_change_password_success(
    change_password_api: ChangePassword,
    walter_authenticator: WalterAuthenticator,
    walter_db: WalterDB,
) -> None:
    old_password = walter_db.get_user("walter@gmail.com").password_hash
    event = get_change_password_event(
        token=walter_authenticator.generate_change_password_token("walter@gmail.com"),
        new_password="new-password",
    )
    expected_response = get_expected_response(
        api_name=change_password_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.SUCCESS,
        message="Successfully changed password!",
    )
    assert expected_response == change_password_api.invoke(event)
    new_password = walter_db.get_user("walter@gmail.com").password_hash
    assert old_password != new_password


def test_change_password_failure_not_authenticated(
    change_password_api: ChangePassword,
    walter_authenticator: WalterAuthenticator,
    walter_db: WalterDB,
) -> None:
    old_password = walter_db.get_user("walter@gmail.com").password_hash
    event = get_change_password_event(
        token=walter_authenticator.generate_change_password_token("walter@gmail.com"),
        new_password="new-password",
    )
    headers = event["headers"]
    headers["Authorization"] = "Bearer INVALID_TOKEN"
    event["headers"] = headers
    expected_response = get_expected_response(
        api_name=change_password_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Not authenticated!",
    )
    assert expected_response == change_password_api.invoke(event)
    new_password = walter_db.get_user("walter@gmail.com").password_hash
    assert old_password == new_password  # assert user pass word has not changed
