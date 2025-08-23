import json

import pytest

from src.api.auth.refresh.method import Refresh
from src.api.common.models import HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from tst.api.utils import get_expected_response


@pytest.fixture
def refresh_api(
    walter_authenticator: WalterAuthenticator,
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
) -> Refresh:
    return Refresh(walter_authenticator, walter_cw, walter_db)


def _event_with_refresh(token: str) -> dict:
    return {
        "headers": {
            "Authorization": f"Bearer {token}",
        },
        "queryStringParameters": None,
        "body": json.dumps({}),
    }


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

    event = _event_with_refresh(tokens.refresh_token)

    # Act
    response = refresh_api.invoke(event)

    # Assert
    assert response.http_status == HTTPStatus.OK
    assert response.status == Status.SUCCESS
    assert response.message == "Access token refreshed!"
    assert "access_token" in response.data
    assert "access_token_expiration" in response.data


def test_refresh_failure_missing_token(refresh_api: Refresh) -> None:
    event = {
        "headers": {},
        "queryStringParameters": None,
        "body": json.dumps({}),
    }

    expected_response = get_expected_response(
        api_name=refresh_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Client bad request! Missing required header: 'authorization : Bearer '",
    )

    assert expected_response == refresh_api.invoke(event)


def test_refresh_failure_invalid_token(refresh_api: Refresh) -> None:
    event = _event_with_refresh("invalid-token")

    expected_response = get_expected_response(
        api_name=refresh_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Not authenticated! Refresh token is invalid or expired.",
    )

    assert expected_response == refresh_api.invoke(event)


def test_refresh_failure_session_does_not_exist(
    refresh_api: Refresh, walter_authenticator: WalterAuthenticator
) -> None:
    tokens = walter_authenticator.generate_tokens("user-001")

    # Do NOT create the corresponding session
    event = _event_with_refresh(tokens.refresh_token)

    expected_response = get_expected_response(
        api_name=refresh_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
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

    event = _event_with_refresh(tokens.refresh_token)

    expected_response = get_expected_response(
        api_name=refresh_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
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

    event = _event_with_refresh(tokens.refresh_token)

    expected_response = get_expected_response(
        api_name=refresh_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Session has been revoked!",
    )

    assert expected_response == refresh_api.invoke(event)
