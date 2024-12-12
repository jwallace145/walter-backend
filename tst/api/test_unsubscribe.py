import pytest

from src.api.common.models import HTTPStatus, Status
from src.api.unsubscribe import Unsubscribe
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from tst.api.utils import get_unsubscribe_event, get_expected_response


@pytest.fixture
def unsubscribe_api(
    walter_authenticator: WalterAuthenticator,
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
) -> Unsubscribe:
    return Unsubscribe(walter_authenticator, walter_cw, walter_db)


def test_unsubscribe_success(
    unsubscribe_api: Unsubscribe,
    walter_authenticator: WalterAuthenticator,
    walter_db: WalterDB,
) -> None:
    user = walter_db.get_user("walter@gmail.com")
    user.subscribed = True
    walter_db.update_user(user)
    token = walter_authenticator.generate_user_token("walter@gmail.com")
    event = get_unsubscribe_event(token)
    expected_response = get_expected_response(
        api_name=unsubscribe_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.SUCCESS,
        message="Unsubscribed user!",
    )
    assert expected_response == unsubscribe_api.invoke(event)


def test_unsubscribe_failure_already_unsubscribe(
    unsubscribe_api: Unsubscribe,
    walter_authenticator: WalterAuthenticator,
    walter_db: WalterDB,
) -> None:
    user = walter_db.get_user("walter@gmail.com")
    user.subscribed = False
    walter_db.update_user(user)
    token = walter_authenticator.generate_user_token("walter@gmail.com")
    event = get_unsubscribe_event(token)
    expected_response = get_expected_response(
        api_name=unsubscribe_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Email is already unsubscribed!",
    )
    assert expected_response == unsubscribe_api.invoke(event)
