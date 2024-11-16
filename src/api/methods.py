import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from src.api.exceptions import BadRequest, NotAuthenticated
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.utils.log import Logger

log = Logger(__name__).get_logger()

################
# API RESPONSE #
################


class Status(Enum):
    SUCCESS = "Success"
    FAILURE = "Failure"


class HTTPStatus(Enum):
    OK = 200
    CREATED = 201
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


##############
# API METHOD #
##############


class WalterAPIMethod(ABC):

    METRICS_SUCCESS_COUNT = "SuccessCount"
    METRICS_FAILURE_COUNT = "FailureCount"
    METRICS_TOTAL_COUNT = "TotalCount"

    def __init__(
        self,
        api_name: str,
        required_fields: List[str],
        exceptions: List[Exception],
        authenticator: WalterAuthenticator,
        metrics: WalterCloudWatchClient,
    ) -> None:
        self.api_name = api_name
        self.required_fields = required_fields
        self.exceptions = exceptions
        self.authenticator = authenticator
        self.metrics = metrics

    def invoke(self, event: dict) -> dict:
        log.info(f"Invoking {self.api_name} with event:\n{json.dumps(event, indent=4)}")

        response = None
        try:
            self._validate_request(event)

            authenticated_email = None
            if self.is_authenticated_api():
                authenticated_email = self._authenticate_request(event)

            response = self.execute(event, authenticated_email)
        except Exception as exception:
            response = self._handle_exception(exception)
        finally:
            self.emit_metrics(response)

        return response

    def _validate_request(self, event: dict) -> None:
        self._validate_required_fields(event)
        self.validate_fields(event)

    def _validate_required_fields(self, event: dict) -> None:
        log.info(f"Validating required fields: {self.required_fields}")
        body = {}
        if event["body"] is not None:
            body = json.loads(event["body"])
        for field in self.required_fields:
            if field not in body:
                raise BadRequest(
                    f"Client bad request! Missing required field: '{field}'"
                )

    def _authenticate_request(self, event: dict) -> None:
        log.info("Authenticating request")

        token = self.authenticator.get_token(event)
        if token is None:
            raise NotAuthenticated("Not authenticated!")

        decoded_token = self.authenticator.decode_user_token(token)
        if decoded_token is None:
            raise NotAuthenticated("Not authenticated!")

        log.info("Successfully authenticated request!")
        return decoded_token["sub"]

    def _handle_exception(self, exception: Exception) -> dict:
        status = HTTPStatus.INTERNAL_SERVER_ERROR
        for e in self.exceptions:
            if isinstance(exception, e):
                status = HTTPStatus.OK
                break
        return self._create_response(
            status,
            Status.FAILURE,
            str(exception),
        )

    def _create_response(
        self, http_status: HTTPStatus, status: Status, message: str, data: dict = None
    ) -> dict:
        return Response(
            api_name=self.api_name,
            http_status=http_status,
            status=status,
            message=message,
            data=data,
        ).to_json()

    def _get_success_count_metric_name(self) -> str:
        return f"{self.api_name}.{WalterAPIMethod.METRICS_SUCCESS_COUNT}"

    def _get_failure_count_metric_name(self) -> str:
        return f"{self.api_name}.{WalterAPIMethod.METRICS_FAILURE_COUNT}"

    def _get_total_count_metric_name(self) -> str:
        return f"{self.api_name}.{WalterAPIMethod.METRICS_TOTAL_COUNT}"

    def emit_metrics(self, response: dict | None) -> None:
        success = response["statusCode"] == HTTPStatus.OK.value
        self.metrics.emit_metric(
            self._get_success_count_metric_name(), 1 if success else 0
        )
        self.metrics.emit_metric(
            self._get_failure_count_metric_name(), 0 if success else 1
        )
        self.metrics.emit_metric(self._get_total_count_metric_name(), 1)

    @abstractmethod
    def execute(self, event: dict, email: str) -> dict:
        pass

    @abstractmethod
    def validate_fields(self, event: dict) -> None:
        pass

    @abstractmethod
    def is_authenticated_api(self) -> bool:
        pass


#############
# API UTILS #
#############


def is_valid_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def is_valid_username(username: str) -> bool:
    return username.isalnum()
