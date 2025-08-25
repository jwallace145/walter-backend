import json
from dataclasses import dataclass

from src.api.common.models import HTTPStatus, Status


@dataclass
class CanaryResponse:
    """
    WalterCanary - Response
    """

    api_name: str
    status: Status
    response_time_millis: float

    def to_json(self) -> dict:
        return {
            "statusCode": HTTPStatus.OK.value,
            "body": json.dumps(
                {
                    "Canary": self.api_name,
                    "Status": self.status.value,
                    "ResponseTimeMillis": self.response_time_millis,
                }
            ),
        }
