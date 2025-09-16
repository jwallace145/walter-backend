import pytest

from src.api.auth.logout.method import Logout
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Status
from src.api.factory import APIMethod, APIMethodFactory
from src.api.routing.methods import HTTPMethod
from src.auth.authenticator import WalterAuthenticator
from src.database.client import WalterDB
from tst.api.utils import UNIT_TEST_REQUEST_ID, get_api_event, get_expected_response

LOGOUT_API_PATH = "/auth/logout"
"""(str): Path to the logout API endpoint."""

LOGOUT_API_METHOD = HTTPMethod.POST
"""(HTTPMethod): HTTP method for the logout API endpoint."""


@pytest.fixture
def logout_api(
    api_method_factory: APIMethodFactory,
) -> WalterAPIMethod:
    return api_method_factory.get_api(APIMethod.LOGOUT, UNIT_TEST_REQUEST_ID)


def test_logout_success(
    logout_api: Logout,
    walter_db: WalterDB,
    walter_authenticator: WalterAuthenticator,
) -> None:
    # Use an existing session from seeded test data
    user_id = "user-001"
    session_id = "session-001"
    access_token, _ = walter_authenticator.generate_access_token(user_id, session_id)

    event = get_api_event(
        LOGOUT_API_PATH,
        LOGOUT_API_METHOD,
        token=access_token,
    )

    response = logout_api.invoke(event)

    assert response.http_status == HTTPStatus.OK
    assert response.status == Status.SUCCESS
    assert response.message == "User logged out successfully!"

    # Verify the session was revoked and ended
    session = walter_db.get_session(user_id, session_id)
    assert session.revoked is True
    assert session.session_end is not None


def test_logout_failure_missing_token(logout_api: Logout) -> None:
    # Missing Authorization header should trigger BadRequest from header validation
    event = get_api_event(LOGOUT_API_PATH, LOGOUT_API_METHOD)

    expected_response = get_expected_response(
        api_name=logout_api.API_NAME,
        status_code=HTTPStatus.BAD_REQUEST,
        status=Status.SUCCESS,
        message="Client bad request! Missing required header: 'authorization : Bearer'",
    )

    assert expected_response == logout_api.invoke(event)


def test_logout_failure_invalid_token(
    logout_api: Logout,
) -> None:
    event = get_api_event(LOGOUT_API_PATH, LOGOUT_API_METHOD, token="invalid-token")

    expected_response = get_expected_response(
        api_name=logout_api.API_NAME,
        status_code=HTTPStatus.UNAUTHORIZED,
        status=Status.SUCCESS,
        message="Not authenticated! Token is expired or invalid.",
    )

    assert expected_response == logout_api.invoke(event)


def test_logout_failure_session_does_not_exist(
    logout_api: Logout, walter_authenticator: WalterAuthenticator
) -> None:
    # generate a valid token for a non-existent session
    user_id = "user-001"
    session_id = "does-not-exist"
    access_token, _ = walter_authenticator.generate_access_token(user_id, session_id)

    event = get_api_event(
        LOGOUT_API_PATH,
        LOGOUT_API_METHOD,
        token=access_token,
    )

    expected_response = get_expected_response(
        api_name=logout_api.API_NAME,
        status_code=HTTPStatus.UNAUTHORIZED,
        status=Status.SUCCESS,
        message="Not authenticated! Session does not exist.",
    )

    assert expected_response == logout_api.invoke(event)
