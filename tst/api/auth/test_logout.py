import json

import pytest

from src.api.auth.logout.method import Logout
from src.api.common.models import HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.database.client import WalterDB
from src.metrics.client import DatadogMetricsClient
from tst.api.utils import get_expected_response


@pytest.fixture
def logout_api(
    walter_authenticator: WalterAuthenticator,
    datadog_metrics: DatadogMetricsClient,
    walter_db: WalterDB,
) -> Logout:
    return Logout(walter_authenticator, datadog_metrics, walter_db)


def _event_with_auth(token: str) -> dict:
    return {
        "headers": {
            "Authorization": f"Bearer {token}",
        },
        "queryStringParameters": None,
        "body": json.dumps({}),
    }


def test_logout_success(
    logout_api: Logout,
    walter_db: WalterDB,
    walter_authenticator: WalterAuthenticator,
) -> None:
    # Use an existing session from seeded test data
    user_id = "user-001"
    session_id = "session-001"
    access_token, _ = walter_authenticator.generate_access_token(user_id, session_id)

    event = _event_with_auth(access_token)

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
    event = {
        "headers": {},
        "queryStringParameters": None,
        "body": json.dumps({}),
    }

    expected_response = get_expected_response(
        api_name=logout_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Client bad request! Missing required header: 'authorization : Bearer'",
    )

    assert expected_response == logout_api.invoke(event)


def test_logout_failure_invalid_token(
    logout_api: Logout,
) -> None:
    event = _event_with_auth("invalid-token")

    expected_response = get_expected_response(
        api_name=logout_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
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

    event = _event_with_auth(access_token)

    expected_response = get_expected_response(
        api_name=logout_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Not authenticated! Session does not exist.",
    )

    assert expected_response == logout_api.invoke(event)
