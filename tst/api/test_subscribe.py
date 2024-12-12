import pytest

from src.api.common.models import HTTPStatus, Status
from src.api.subscribe import Subscribe
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from tst.api.utils import get_subscribe_event, get_expected_response


@pytest.fixture
def subscribe_api(
    walter_authenticator: WalterAuthenticator,
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
) -> Subscribe:
    return Subscribe(walter_authenticator, walter_cw, walter_db)


def test_subscribe_success(
    subscribe_api: Subscribe,
    walter_authenticator: WalterAuthenticator,
    walter_db: WalterDB,
) -> None:
    user = walter_db.get_user("walter@gmail.com")
    user.subscribed = False
    walter_db.update_user(user)
    token = walter_authenticator.generate_user_token("walter@gmail.com")
    event = get_subscribe_event(token)
    expected_response = get_expected_response(
        api_name=subscribe_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.SUCCESS,
        message="Subscribed user!",
    )
    assert expected_response == subscribe_api.invoke(event)


def test_subscribe_failure_already_subscribed(
    subscribe_api: Subscribe,
    walter_authenticator: WalterAuthenticator,
    walter_db: WalterDB,
) -> None:
    user = walter_db.get_user("walter@gmail.com")
    user.subscribed = True
    walter_db.update_user(user)
    token = walter_authenticator.generate_user_token("walter@gmail.com")
    event = get_subscribe_event(token)
    expected_response = get_expected_response(
        api_name=subscribe_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Email already subscribed!",
    )
    assert expected_response == subscribe_api.invoke(event)
