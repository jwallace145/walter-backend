import json
from enum import Enum

from dataclasses import dataclass


class Status(Enum):
    SUCCESS = "Success"
    FAILURE = "Failure"


class HTTPStatus(Enum):
    OK = 200
    BAD_REQUEST = 400
    INTERNAL_SERVER_ERROR = 500


@dataclass
class Response:

    api_name: str
    http_status: HTTPStatus
    status: Status
    message: str

    def to_json(self) -> dict:
        return {
            "statusCode": self.http_status.value,
            "body": json.dumps(
                {
                    "API": self.api_name,
                    "Status": self.status.value,
                    "Message": self.message,
                }
            ),
        }


def create_response(
    name: str, http_status: HTTPStatus, status: Status, message: str
) -> dict:
    return Response(
        api_name=name,
        http_status=http_status,
        status=status,
        message=message,
    ).to_json()
