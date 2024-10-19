import json
from dataclasses import dataclass
from enum import Enum


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
