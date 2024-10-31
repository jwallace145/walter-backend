import pytest

from src.api.get_user import GetUser
from src.api.methods import HTTPStatus, Status
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from tst.api.utils import get_get_user_event, get_expected_response


@pytest.fixture
def get_user_api(
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
    walter_sm: WalterSecretsManagerClient,
) -> GetUser:
    return GetUser(walter_cw, walter_db, walter_sm)


def test_get_user(get_user_api: GetUser, jwt_walter: str) -> None:
    event = get_get_user_event(token=jwt_walter)
    expected_response = get_expected_response(
        api_name=get_user_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.SUCCESS,
        message="Successfully retrieved user!",
        data={
            "email": "walter@gmail.com",
            "username": "walter",
        },
    )
    assert expected_response == get_user_api.invoke(event)


def test_get_user_failure_user_does_not_exist(get_user_api: GetUser) -> None:
    event = get_get_user_event(token="invalid-token")
    expected_response = get_expected_response(
        api_name=get_user_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Not authenticated!",
    )
    assert expected_response == get_user_api.invoke(event)
