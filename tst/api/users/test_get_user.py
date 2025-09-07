import pytest

from src.api.common.methods import HTTPStatus, Status
from src.api.routing.methods import HTTPMethod
from src.api.users.get_user import GetUser
from src.auth.authenticator import WalterAuthenticator
from src.aws.s3.client import WalterS3Client
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.environment import Domain
from src.metrics.client import DatadogMetricsClient
from tst.api.utils import get_api_event, get_expected_response

GET_USER_API_PATH = "/users"
"""(str): Path to the get user API endpoint."""

GET_USER_API_METHOD = HTTPMethod.GET
"""(HTTPMethod): HTTP method for the get user API endpoint."""


@pytest.fixture
def get_user_api(
    walter_authenticator: WalterAuthenticator,
    datadog_metrics: DatadogMetricsClient,
    walter_db: WalterDB,
    walter_sm: WalterSecretsManagerClient,
    walter_s3: WalterS3Client,
) -> GetUser:
    return GetUser(
        Domain.TESTING,
        walter_authenticator,
        datadog_metrics,
        walter_db,
        walter_sm,
        walter_s3,
    )


# def test_get_user(get_user_api: GetUser, jwt_walter: str) -> None:
#     event = get_get_user_event(token=jwt_walter)
#     utc_now = datetime.datetime.now(datetime.UTC)
#     expected_response = get_expected_response(
#         api_name=get_user_api.API_NAME,
#         status_code=HTTPStatus.OK,
#         status=Status.SUCCESS,
#         message="Successfully retrieved user!",
#         data={
#             "email": "walter@gmail.com",
#             "username": "walter",
#             "verified": True,
#             "subscribed": True,
#             "sign_up_date": datetime.datetime(
#                 year=2024, month=1, day=1, hour=0, minute=0, second=0, microsecond=0
#             ).strftime("%Y-%m-%d"),
#             "last_active_date": utc_now.strftime("%Y-%m-%d"),
#             "free_trial_end_date": datetime.datetime(
#                 year=2024, month=1, day=31, hour=0, minute=0, second=0, microsecond=0
#             ).strftime("%Y-%m-%d"),
#             "active_stripe_subscription": True,
#         },
#     )
#     assert expected_response == get_user_api.invoke(event)


def test_get_user_failure_user_does_not_exist(get_user_api: GetUser) -> None:
    event = get_api_event(
        GET_USER_API_PATH, GET_USER_API_METHOD, token="invalid-token", body=None
    )
    expected_response = get_expected_response(
        api_name=get_user_api.API_NAME,
        status_code=HTTPStatus.UNAUTHORIZED,
        status=Status.SUCCESS,
        message="Not authenticated! Token is expired or invalid.",
    )
    assert expected_response == get_user_api.invoke(event)
