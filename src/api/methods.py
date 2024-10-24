import json
from abc import ABC, abstractmethod
from typing import List

from src.api.exceptions import BadRequest, NotAuthenticated
from src.api.models import HTTPStatus, Response, Status
from src.api.utils import get_token
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.utils.auth import decode_token
from src.utils.log import Logger

log = Logger(__name__).get_logger()


class WalterAPIMethod(ABC):

    METRICS_SUCCESS_COUNT = "SuccessCount"
    METRICS_FAILURE_COUNT = "FailureCount"
    METRICS_TOTAL_COUNT = "TotalCount"

    def __init__(
        self,
        api_name: str,
        required_fields: List[str],
        exceptions: List[Exception],
        metrics: WalterCloudWatchClient,
    ) -> None:
        self.api_name = api_name
        self.required_fields = required_fields
        self.exceptions = exceptions
        self.metrics = metrics

    def invoke(self, event: dict) -> dict:
        log.info(f"Invoking {self.api_name} with event:\n{json.dumps(event, indent=4)}")

        response = None
        try:
            self._validate_request(event)

            if self.is_authenticated_api():
                self._authenticate_request(event)

            response = self.execute(event)
        except Exception as exception:
            response = self._handle_exception(exception)
        finally:
            self.emit_metrics(response)

        return response

    def _validate_request(self, event: dict) -> None:
        self._validate_required_fields(event)
        self.validate_fields(event)

    def _validate_required_fields(self, event: dict) -> None:
        body = json.loads(event["body"])
        for field in self.required_fields:
            if field not in body:
                raise BadRequest(
                    f"Client bad request! Missing required field: '{field}'"
                )

    def _authenticate_request(self, event: dict) -> None:
        log.info("Authenticating request")
        token = get_token(event)
        if token is None:
            raise NotAuthenticated("Not authenticated!")

        decoded_token = decode_token(token, self.get_jwt_secret_key())
        if decoded_token is None:
            raise NotAuthenticated("Not authenticated!")

        body = json.loads(event["body"])
        email = body["email"]

        authenticated_user = decoded_token["sub"]
        if email != authenticated_user:
            raise NotAuthenticated("Not authenticated!")
        log.info("Successfully authenticated request!")

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
    def execute(self, event: dict) -> dict:
        pass

    @abstractmethod
    def validate_fields(self, event: dict) -> None:
        pass

    @abstractmethod
    def is_authenticated_api(self) -> bool:
        pass

    @abstractmethod
    def get_jwt_secret_key(self) -> str:
        pass
