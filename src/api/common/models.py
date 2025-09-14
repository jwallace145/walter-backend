import json
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from src.environment import Domain


class Status(Enum):
    """
    The status of the API response.
    """

    SUCCESS = "Success"
    FAILURE = "Failure"

    @staticmethod
    def from_string(status: str):
        for status_enum in Status:
            if status_enum.value.lower() == status.lower():
                return status_enum
        raise ValueError(f"{status} is not a valid status!")


class HTTPStatus(Enum):
    """
    The HTTP status of the API response.

    For more information, see https://developer.mozilla.org/en-US/docs/Web/HTTP/Status.
    """

    OK = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    NOT_FOUND = 404
    CONFLICT = 409
    INTERNAL_SERVER_ERROR = 500

    def is_success(self) -> bool:
        return str(self.value).startswith("2")


@dataclass(kw_only=True)
class Response:
    """
    WalterAPI - Response
    """

    HEADERS = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET,OPTIONS,POST,PUT,DELETE",
    }

    domain: Domain
    api_name: str
    request_id: str
    http_status: HTTPStatus
    status: Status
    message: str
    response_time_millis: Optional[float] = (
        None  # optional response time can be included in response
    )
    data: Optional[dict] = None  # optional data can be included in response

    def to_json(self) -> dict:
        body = {
            "Service": "WalterBackend-API",
            "Domain": self.domain.value,
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

        return {
            "statusCode": self.http_status.value,
            "headers": Response.HEADERS,
            "body": json.dumps(body),
        }

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
