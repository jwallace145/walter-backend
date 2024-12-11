from enum import Enum
from typing import Optional
from dataclasses import dataclass
import json


class Status(Enum):
    """
    The status of the API response.
    """

    SUCCESS = "Success"
    FAILURE = "Failure"


class HTTPStatus(Enum):
    """
    The HTTP status of the API response.

    For more information, see https://developer.mozilla.org/en-US/docs/Web/HTTP/Status.
    """

    OK = 200
    CREATED = 201
    BAD_REQUEST = 400
    INTERNAL_SERVER_ERROR = 500


@dataclass
class Response:
    """
    WalterAPI - Response
    """

    HEADERS = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET,OPTIONS,POST,DELETE",
    }

    api_name: str
    http_status: HTTPStatus
    status: Status
    message: str
    data: Optional[dict] = None  # optional data can be included in response

    def to_json(self) -> dict:
        body = {
            "API": self.api_name,
            "Status": self.status.value,
            "Message": self.message,
        }

        # if data is included, add to response dict
        if self.data is not None:
            body["Data"] = self.data

        return {
            "statusCode": self.http_status.value,
            "headers": Response.HEADERS,
            "body": json.dumps(body),
        }
