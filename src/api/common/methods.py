import json
from abc import ABC, abstractmethod
from typing import List, Dict

from src.api.common.exceptions import BadRequest, NotAuthenticated
from src.api.common.models import HTTPStatus, Status, Response
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.utils.log import Logger

log = Logger(__name__).get_logger()

###########
# METRICS #
###########

# Metrics included in this file are emitted for all APIs

METRICS_SUCCESS_COUNT = "SuccessCount"
"""The number of successful API invocations."""

METRICS_FAILURE_COUNT = "FailureCount"
"""The number of failed API invocations."""

METRICS_TOTAL_COUNT = "TotalCount"
"""The total number of API invocations."""

#########################################
# WALTER API ABSTRACT BASE METHOD CLASS #
#########################################


class WalterAPIMethod(ABC):
    """
    WalterAPI - Method

    This class contains the core, undifferentiated logic for all Walter APIs.
    """

    def __init__(
        self,
        api_name: str,
        required_query_fields: List[str],
        required_headers: Dict[str, str],
        required_fields: List[str],
        exceptions: List[Exception],
        authenticator: WalterAuthenticator,
        metrics: WalterCloudWatchClient,
    ) -> None:
        self.api_name = api_name
        self.required_query_fields = required_query_fields
        self.required_headers = required_headers
        self.required_fields = required_fields
        self.exceptions = exceptions
        self.authenticator = authenticator
        self.metrics = metrics

    def invoke(self, event: dict) -> dict:
        """
        Invoke the API.

        This method is the entrypoint for all Walter APIs.

        Args:
            event: The request event of the API invocation.

        Returns:
            The API response.
        """
        log.info(f"Invoking '{self.api_name}' API")
        log.debug(f"Event:\n{json.dumps(event, indent=4)}")

        response = None
        try:
            self._validate_request(event)

            # authenticate request if necessary
            authenticated_email = None
            if self.is_authenticated_api():
                authenticated_email = self._authenticate_request(event)

            response = self.execute(event, authenticated_email)
        except Exception as exception:
            log.error("Error occurred during API invocation!", exc_info=True)
            response = self._handle_exception(exception)
        finally:
            self.emit_metrics(response)

        return response

    def _validate_request(self, event: dict) -> None:
        log.info("Validating request...")
        self._validate_required_query_fields(event)
        self._validate_required_headers(event)
        self._validate_required_fields(event)
        self.validate_fields(event)
        log.info("Successfully validated request!")

    def _validate_required_query_fields(self, event: dict) -> None:
        """
        Validate the request event contains the APIs required query fields.

        Some APIs, particularly GET methods, require query fields in the request URL.
        This validation method ensures that the required query fields are present in the request
        before invoking the core API logic to avoid any unexpected errors.

        Args:
            event: The request event to invoke the API.

        Raises:
            BadRequest exception if any of the APIs required query fields are not
            included in the request.
        """
        # early return if no required query fields
        if len(self.required_query_fields) == 0:
            log.debug("No required query fields to validate!")
            return

        log.debug(f"Validating required query fields: {self.required_query_fields}")
        query_fields = {}
        if event["queryStringParameters"] is not None:
            query_fields = event["queryStringParameters"]
        for field in self.required_query_fields:
            if field not in query_fields:
                raise BadRequest(
                    f"Client bad request! Missing required query field: '{field}'"
                )
        log.debug("Successfully validated required query fields!")

    def _validate_required_headers(self, event: dict) -> None:
        """
        Validate the request event contains the APIs required headers.

        Args:
            event: The request event to invoke the API.

        Raises:
            BadRequest exception if any of the APIs required headers are not
            included in the request.
        """
        # early return if no required headers
        if len(self.required_headers) == 0:
            log.debug("No required headers to validate!")
            return

        log.debug(f"Validating required headers: {self.required_headers}")
        # lowercase the headers for case-insensitive verification
        headers = {key.lower(): value for key, value in event["headers"].items()}
        for key, value in self.required_headers.items():
            if key.lower() not in headers or value not in headers[key.lower()]:
                raise BadRequest(
                    f"Client bad request! Missing required header: '{key} : {value}'"
                )
        log.debug("Successfully validated required headers!")

    def _validate_required_fields(self, event: dict) -> None:
        """
        Validate the APIs required fields are included in the request body.

        Args:
            event: The request event for the API.

        Returns:
            Raises a BadRequest exception if any required fields are missing.
        """
        # early return if no request payload
        if len(self.required_fields) == 0:
            log.debug("No required fields to validate!")
            return

        log.debug(f"Validating required fields: {self.required_fields}")
        body = {}
        if event["body"] is not None:
            body = json.loads(event["body"])
        for field in self.required_fields:
            if field not in body:
                raise BadRequest(
                    f"Client bad request! Missing required field: '{field}'"
                )
        log.debug("Successfully validated required fields!")

    def _authenticate_request(self, event: dict) -> str:
        """
        Authenticate request and return authenticated email.

        This method authenticates requests by verifying the Authorization
        Bearer token in the request header. If the token is valid, the
        request is authenticated.

        Args:
            event: The request event for the API.

        Returns:
            user_email: The email of the authenticated user.
        """
        log.info("Authenticating request")

        token = self.authenticator.get_token(event)
        if token is None:
            raise NotAuthenticated("Not authenticated! Token is null.")

        decoded_token = self.authenticator.decode_user_token(token)
        if decoded_token is None:
            raise NotAuthenticated("Not authenticated! Token is invalid.")

        user_email = decoded_token["sub"]
        log.info(f"Successfully authenticated request for user '{user_email}'!")

        return user_email

    def _handle_exception(self, exception: Exception) -> dict:
        """
        Handle exceptions thrown during API invocation.

        Each API includes a list of expected exceptions that can be handled successfully.
        These exceptions cause the API to return a Failure status, but a successful HTTPStatus.
        Unknown exceptions are caught and ultimately rethrown as server internal errors with a
        HTTPStatus of 500.

        Args:
            exception: The exception thrown during API invocation.

        Returns:
            The API response for the exception.
        """
        # assume server internal error
        status = HTTPStatus.INTERNAL_SERVER_ERROR

        # if exception is an expected exception, change http status to ok
        for e in self.exceptions:
            if isinstance(exception, e):
                status = HTTPStatus.OK
                break

        # return failure response
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

    def emit_metrics(self, response: dict) -> None:
        """
        Emit the common metrics for the API.

        Args:
            response: The API response object.
        """
        log.info(f"Emitting metrics for '{self.api_name}' API")
        success = response["statusCode"] == HTTPStatus.OK.value
        self.metrics.emit_metric(
            self._get_success_count_metric_name(), 1 if success else 0
        )
        self.metrics.emit_metric(
            self._get_failure_count_metric_name(), 0 if success else 1
        )
        self.metrics.emit_metric(self._get_total_count_metric_name(), 1)

    def _get_success_count_metric_name(self) -> str:
        return f"{self.api_name}.{METRICS_SUCCESS_COUNT}"

    def _get_failure_count_metric_name(self) -> str:
        return f"{self.api_name}.{METRICS_FAILURE_COUNT}"

    def _get_total_count_metric_name(self) -> str:
        return f"{self.api_name}.{METRICS_TOTAL_COUNT}"

    @abstractmethod
    def execute(self, event: dict, email: str) -> dict:
        """
        The core action implemented by the API.
        """
        pass

    @abstractmethod
    def validate_fields(self, event: dict) -> None:
        """
        Additional validations on the request fields.
        """
        pass

    @abstractmethod
    def is_authenticated_api(self) -> bool:
        """
        APIs that require authentication should return True.
        """
        pass

    @staticmethod
    def get_query_field(event: dict, field: str) -> str:
        return event["queryStringParameters"][field]
