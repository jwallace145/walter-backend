import pytest

from src.api.auth.refresh.method import Refresh
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Status
from src.api.factory import APIMethod, APIMethodFactory
from src.api.routing.methods import HTTPMethod
from src.auth.authenticator import WalterAuthenticator
from src.database.client import WalterDB
from tst.api.utils import get_api_event, get_expected_response

REFRESH_API_PATH = "/auth/refresh"
"""(str): Path to the refresh API endpoint."""

REFRESH_API_METHOD = HTTPMethod.POST
"""(HTTPMethod): HTTP method for the refresh API endpoint."""


@pytest.fixture
def refresh_api(
    api_method_factory: APIMethodFactory,
) -> WalterAPIMethod:
    return api_method_factory.get_api(APIMethod.REFRESH)


def test_refresh_success(
    refresh_api: Refresh,
    walter_authenticator: WalterAuthenticator,
    walter_db: WalterDB,
) -> None:
    # Arrange: create a session matching a generated refresh token
    user_id = "user-001"
    tokens = walter_authenticator.generate_tokens(user_id)

    # Create a session with the JTI from tokens
    walter_db.create_session(
        user_id=user_id,
        token_id=tokens.jti,
        ip_address="127.0.0.1",
        device="pytest/1.0",
    )

    event = get_api_event(
        REFRESH_API_PATH,
        REFRESH_API_METHOD,
        token=tokens.refresh_token,
    )

    # Act
    response = refresh_api.invoke(event)

    # Assert
    assert response.http_status == HTTPStatus.OK
    assert response.status == Status.SUCCESS
    assert response.message == "Access token refreshed!"
    assert "user_id" in response.data
    assert "access_token" in response.data
    assert "access_token_expires_at" in response.data


def test_refresh_failure_missing_token(refresh_api: Refresh) -> None:
    event = get_api_event(REFRESH_API_PATH, REFRESH_API_METHOD)

    expected_response = get_expected_response(
        api_name=refresh_api.API_NAME,
        status_code=HTTPStatus.BAD_REQUEST,
        status=Status.SUCCESS,
        message="Client bad request! Missing required header: 'authorization : Bearer '",
    )

    assert expected_response == refresh_api.invoke(event)


def test_refresh_failure_invalid_token(refresh_api: Refresh) -> None:
    event = get_api_event(REFRESH_API_PATH, REFRESH_API_METHOD, token="invalid-token")

    expected_response = get_expected_response(
        api_name=refresh_api.API_NAME,
        status_code=HTTPStatus.UNAUTHORIZED,
        status=Status.SUCCESS,
        message="Not authenticated! Refresh token is invalid or expired.",
    )

    assert expected_response == refresh_api.invoke(event)


def test_refresh_failure_session_does_not_exist(
    refresh_api: Refresh, walter_authenticator: WalterAuthenticator
) -> None:
    tokens = walter_authenticator.generate_tokens("user-001")

    # Do NOT create the corresponding session
    event = get_api_event(
        REFRESH_API_PATH, REFRESH_API_METHOD, token=tokens.refresh_token
    )

    expected_response = get_expected_response(
        api_name=refresh_api.API_NAME,
        status_code=HTTPStatus.UNAUTHORIZED,
        status=Status.SUCCESS,
        message="Session does not exist!",
    )

    assert expected_response == refresh_api.invoke(event)


def test_refresh_failure_session_expired(
    refresh_api: Refresh, walter_authenticator: WalterAuthenticator, walter_db: WalterDB
) -> None:
    # Create token and a session, then backdate the session expiration to past
    user_id = "user-001"
    tokens = walter_authenticator.generate_tokens(user_id)

    session = walter_db.create_session(
        user_id=user_id, token_id=tokens.jti, ip_address="127.0.0.1", device="pytest"
    )
    # set expiration in the past
    session.session_expiration = session.session_start.replace(year=2000)
    walter_db.update_session(session)

    event = get_api_event(
        REFRESH_API_PATH, REFRESH_API_METHOD, token=tokens.refresh_token
    )

    expected_response = get_expected_response(
        api_name=refresh_api.API_NAME,
        status_code=HTTPStatus.UNAUTHORIZED,
        status=Status.SUCCESS,
        message="Session has expired!",
    )

    assert expected_response == refresh_api.invoke(event)


def test_refresh_failure_session_revoked(
    refresh_api: Refresh, walter_authenticator: WalterAuthenticator, walter_db: WalterDB
) -> None:
    user_id = "user-001"
    tokens = walter_authenticator.generate_tokens(user_id)

    session = walter_db.create_session(
        user_id=user_id, token_id=tokens.jti, ip_address="127.0.0.1", device="pytest"
    )
    session.revoked = True
    walter_db.update_session(session)

    event = get_api_event(
        REFRESH_API_PATH, REFRESH_API_METHOD, token=tokens.refresh_token
    )

    expected_response = get_expected_response(
        api_name=refresh_api.API_NAME,
        status_code=HTTPStatus.UNAUTHORIZED,
        status=Status.SUCCESS,
        message="Session has been revoked!",
    )

    assert expected_response == refresh_api.invoke(event)
