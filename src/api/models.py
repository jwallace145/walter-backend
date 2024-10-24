import json
from dataclasses import dataclass
from enum import Enum
from typing import Optional


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
    data: Optional[dict] = None

    def to_json(self) -> dict:
        body = {
            "API": self.api_name,
            "Status": self.status.value,
            "Message": self.message,
        }

        if self.data is not None:
            body["Data"] = self.data

        return {
            "statusCode": self.http_status.value,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET,OPTIONS,POST",
            },
            "body": json.dumps(body),
        }
