import datetime

import pytest

from src.api.get_user import GetUser
from src.api.common.methods import HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from tst.api.utils import get_get_user_event, get_expected_response


@pytest.fixture
def get_user_api(
    walter_authenticator: WalterAuthenticator,
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
    walter_sm: WalterSecretsManagerClient,
) -> GetUser:
    return GetUser(walter_authenticator, walter_cw, walter_db, walter_sm)


def test_get_user(get_user_api: GetUser, jwt_walter: str) -> None:
    event = get_get_user_event(token=jwt_walter)
    utc_now = datetime.datetime.now(datetime.UTC)
    expected_response = get_expected_response(
        api_name=get_user_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.SUCCESS,
        message="Successfully retrieved user!",
        data={
            "email": "walter@gmail.com",
            "username": "walter",
            "verified": True,
            "subscribed": True,
            "sign_up_date": datetime.datetime(
                year=2024, month=1, day=1, hour=0, minute=0, second=0, microsecond=0
            ).strftime("%Y-%m-%d"),
            "last_active_date": utc_now.strftime("%Y-%m-%d"),
            "free_trial_end_date": datetime.datetime(
                year=2024, month=1, day=31, hour=0, minute=0, second=0, microsecond=0
            ).strftime("%Y-%m-%d"),
            "stripe_customer_id": "stripe-customer-id-walter",
            "stripe_subscription_id": "stripe-subscription-id-walter",
        },
    )
    assert expected_response == get_user_api.invoke(event)


def test_get_user_failure_user_does_not_exist(get_user_api: GetUser) -> None:
    event = get_get_user_event(token="invalid-token")
    expected_response = get_expected_response(
        api_name=get_user_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Not authenticated! Token is invalid.",
    )
    assert expected_response == get_user_api.invoke(event)
