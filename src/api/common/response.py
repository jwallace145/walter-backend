import json
from dataclasses import dataclass
from typing import Optional

from src.api.common.models import HTTPStatus, Status
from src.environment import Domain


@dataclass(kw_only=True)
class Response:
    """
    WalterAPI - Response
    """

    SERVICE_NAME = "WalterBackend-API"

    domain: Domain
    api_name: str
    request_id: str
    http_status: HTTPStatus
    status: Status
    message: str
    response_time_millis: Optional[float] = (
        None  # optional response time can be included in response
    )
    cookies: Optional[dict] = None  # optional cookies can be included in response
    data: Optional[dict] = None  # optional data can be included in response
    expire_cookies: Optional[bool] = False

    def to_json(self) -> dict:
        headers = self._get_headers()
        multivalue_headers = self._get_multivalue_headers()
        body = self._get_body()
        return self._get_response(headers, multivalue_headers, body)

    def _get_headers(self) -> dict:
        headers = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
            "Access-Control-Allow-Origin": "*",  # TODO: This should be updated for production
            "Access-Control-Allow-Methods": "GET,OPTIONS,POST,PUT,DELETE",
        }
        return headers

    def _get_multivalue_headers(self) -> dict:
        # create cookie headers if cookies are included in response
        multivalue_headers = {}
        if self.cookies is not None:
            cookie_headers = []
            for cookie_name, cookie_value in self.cookies.items():
                cookie = f"{cookie_name}={cookie_value}"

                # set cookie security attributes based on domain
                match self.domain:
                    case Domain.DEVELOPMENT:
                        # do not set secure for development domain
                        cookie += "; Path=/; HttpOnly; SameSite=Strict"
                    case Domain.STAGING:
                        cookie += "; Path=/; HttpOnly; Secure; SameSite=Strict"
                    case Domain.PRODUCTION:
                        cookie += "; Path=/; HttpOnly; Secure; SameSite=Strict"

                if self.expire_cookies:
                    cookie += "; Expires=Thu, 01 Jan 1970 00:00:01 GMT"

                cookie_headers.append(cookie)
            multivalue_headers["Set-Cookie"] = cookie_headers
        return multivalue_headers

    def _get_body(self) -> dict:
        body = {
            "Service": self.SERVICE_NAME,
            "Domain": self.domain.name,
            "API": self.api_name,
            "RequestId": self.request_id,
            "Status": self.status.value,
            "Message": self.message,
        }

        # if response time millis is set, add to response body obj
        if self.response_time_millis is not None:
            body["ResponseTimeMillis"] = self.response_time_millis

        # if data is included, add to response dict
        if self.data is not None:
            body["Data"] = self.data

        return body

    def _get_response(
        self, headers: dict, multivalue_headers: dict, body: dict
    ) -> dict:
        response = {
            "statusCode": self.http_status.value,
        }

        # conditionally add headers and body to response
        if headers is not None and len(headers) > 0:
            response["headers"] = headers
        if multivalue_headers is not None and len(multivalue_headers) > 0:
            response["multiValueHeaders"] = multivalue_headers
        if body is not None and len(body) > 0:
            response["body"] = json.dumps(body)

        return response

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Response):
            return False
        return (
            self.api_name == other.api_name
            and self.http_status == other.http_status
            and self.status == other.status
            and self.message == other.message
            and self.data == other.data
        )
