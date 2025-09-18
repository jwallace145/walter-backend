from src.api.common.models import HTTPStatus, Response, Status
from src.environment import Domain


def test_api_response_with_cookies_dev():
    expected_cookie_settings = [
        "Path=/",
        "HttpOnly",
    ]
    response = Response(
        domain=Domain.DEVELOPMENT,
        api_name="TestAPI",
        request_id="test-request-id",
        http_status=HTTPStatus.OK,
        status=Status.SUCCESS,
        message="Success!",
        cookies={
            "test-cookie": "test-cookie-value",
        },
    )
    response_json = response.to_json()
    cookies = response_json["multiValueHeaders"]["Set-Cookie"]
    assert len(cookies) == 1
    cookie = cookies[0]
    assert cookie.startswith("test-cookie=test-cookie-value;")
    for setting in expected_cookie_settings:
        assert setting in cookie


def test_api_response_with_cookies_prod():
    expected_cookie_settings = [
        "Path=/",
        "HttpOnly",
        "Secure",
        "SameSite=Strict",
    ]
    response = Response(
        domain=Domain.PRODUCTION,
        api_name="TestAPI",
        request_id="test-request-id",
        http_status=HTTPStatus.OK,
        status=Status.SUCCESS,
        message="Success!",
        cookies={
            "test-cookie": "test-cookie-value",
        },
    )
    response_json = response.to_json()
    cookies = response_json["multiValueHeaders"]["Set-Cookie"]
    assert len(cookies) == 1
    cookie = cookies[0]
    assert cookie.startswith("test-cookie=test-cookie-value;")
    for setting in expected_cookie_settings:
        assert setting in cookie
