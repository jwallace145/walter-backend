import pytest
from requests.cookies import RequestsCookieJar

from src.canaries.auth.login import Login
from src.canaries.common.exceptions import CanaryFailure
from src.factory import ClientFactory


@pytest.fixture
def login_canary(
    client_factory: ClientFactory,
) -> Login:
    return Login(
        authenticator=client_factory.get_authenticator(),
        db=client_factory.get_db_client(),
        metrics=client_factory.get_metrics_client(),
    )


def test_login_canary_validate_cookies_success(login_canary: Login) -> None:
    jar: RequestsCookieJar = RequestsCookieJar()
    jar.set("WALTER_BACKEND_ACCESS_TOKEN", "test-access-token")
    jar.set("WALTER_BACKEND_REFRESH_TOKEN", "test-refresh-token")
    login_canary.validate_cookies(jar)


def test_login_canary_validate_cookies_failure(login_canary: Login) -> None:
    jar: RequestsCookieJar = RequestsCookieJar()
    with pytest.raises(Exception):
        login_canary.validate_cookies(jar)


def test_login_canary_validate_data_success(login_canary: Login) -> None:
    data = {
        "user_id": "user-001",
        "access_token_expires_at": "2023-09-20T12:00:00Z",
        "refresh_token_expires_at": "2023-09-20T12:00:00Z",
    }
    login_canary.validate_data(data)


def test_login_canary_validate_data_failure(login_canary: Login) -> None:
    data = {
        "user_id": "user-001",
        "access_token_expires_at": "2023-09-20T12:00:00Z",
        "refresh_token_expires_at": "2023-09-20T12:00:00Z",
        "access_token": "test-access-token",
        "refresh_token": "test-refresh-token",
    }
    with pytest.raises(CanaryFailure):
        login_canary.validate_data(data)
