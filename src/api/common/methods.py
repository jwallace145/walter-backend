import datetime as dt
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from src.api.common.exceptions import BadRequest, NotAuthenticated, UserDoesNotExist
from src.api.common.metrics import (
    METRICS_FAILURE,
    METRICS_RESPONSE_TIME_MILLISECONDS,
    METRICS_SUCCESS,
)
from src.api.common.models import HTTPStatus, Response, Status
from src.auth.authenticator import WalterAuthenticator
from src.database.client import WalterDB
from src.database.sessions.models import Session
from src.database.users.models import User
from src.metrics.client import DatadogMetricsClient
from src.utils.log import Logger

log = Logger(__name__).get_logger()


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
        metrics: DatadogMetricsClient,
        db: WalterDB,
    ) -> None:
        self.api_name = api_name
        self.required_query_fields = required_query_fields
        self.required_headers = required_headers
        self.required_fields = required_fields
        self.exceptions = exceptions
        self.authenticator = authenticator
        self.metrics = metrics
        self.db = db

    def invoke(self, event: dict, emit_metrics: bool = True) -> Response:
        """
        Invoke the API.

        This method is the entrypoint for all Walter APIs.

        Args:
            event: The request event of the API invocation.
            emit_metrics: Emit metrics for the API invocation.

        Returns:
            The API response.
        """
        log.info(f"Invoking '{self.api_name}' API")
        log.debug(f"Event:\n{json.dumps(event, indent=4)}")

        # start timing the invocation for response time metrics
        start = dt.datetime.now(dt.UTC)

        response = None
        try:
            self._validate_request(event)

            # authenticate request if necessary
            session = None
            if self.is_authenticated_api():
                session = self._authenticate_request(event)

            response = self.execute(event, session)
        except Exception as exception:
            log.error("Error occurred during API invocation!", exc_info=True)
            response = self._handle_exception(exception)
        finally:
            # get invocation time in millis and add to response
            end = dt.datetime.now(dt.UTC)
            response.response_time_millis = (end - start).total_seconds() * 1000

            # emit api metrics after adding elapsed time to response obj
            if emit_metrics:
                self._emit_metrics(response)
            else:
                log.info(f"Not emitting metrics for '{self.api_name}' API!")

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
            if field not in query_fields or query_fields[field] is None:
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
        headers = {
            key.lower(): value for key, value in event.get("headers", {}).items()
        }
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
            if field not in body or body[field] is None:
                raise BadRequest(
                    f"Client bad request! Missing required field: '{field}'"
                )
        log.debug("Successfully validated required fields!")

    def _authenticate_request(self, event: dict) -> Session:
        """
        Authenticate API request using Bearer access token.

        This method authenticates requests by verifying the Authorization
        Bearer access token in the request header. If the token is valid,
        the request is authenticated on behalf of the user. The authenticated
        session is returned to the caller.

        Args:
            event: The request event for the API.

        Returns:
            session: The authenticated user session object.
        """
        log.info("Authenticating request")

        token = self.authenticator.get_bearer_token(event)
        if token is None:
            raise NotAuthenticated("Not authenticated! Token is null.")

        decoded = self.authenticator.decode_access_token(token)
        if decoded is None:
            raise NotAuthenticated("Not authenticated! Token is expired or invalid.")
        user_id, jti = decoded

        session = self.db.get_session(user_id, jti)
        if session is None:
            raise NotAuthenticated("Not authenticated! Session does not exist.")

        # ensure session is not revoked or expired
        if session.revoked:
            raise NotAuthenticated("Session has been revoked!")
        if session.session_expiration < dt.datetime.now(dt.UTC):
            raise NotAuthenticated("Session has expired!")

        log.info(
            f"Successfully authenticated request for user '{user_id}' and token ID '{jti}'!"
        )

        return session

    def _handle_exception(self, exception: Exception) -> Response:
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
        return Response(
            api_name=self.api_name,
            http_status=status,
            status=Status.FAILURE,
            message=str(exception),
        )

    def _emit_metrics(self, response: Response) -> None:
        """
        Emit the common metrics for the API.

        Args:
            response: The API response object.
        """
        log.info(f"Emitting metrics for '{self.api_name}' API")
        success = response.http_status == HTTPStatus.OK
        self.metrics.emit_metric(
            f"api.{METRICS_SUCCESS}", success, tags={"api": self.api_name}
        )
        self.metrics.emit_metric(
            f"api.{METRICS_FAILURE}", not success, tags={"api": self.api_name}
        )
        response_time_millis = response.response_time_millis
        self.metrics.emit_metric(
            f"api.{METRICS_RESPONSE_TIME_MILLISECONDS}",
            response_time_millis,
            tags={"api": self.api_name},
        )

    def _verify_user_exists(self, user_id: str) -> User:
        """
        Verify the user exists in the database.

        Args:
            user_id: The user ID of the user.

        Returns:
            (User): The user object if the user exists. Else raises UserDoesNotExist exception.
        """
        log.info(f"Verifying user '{user_id}' exists")
        user = self.db.get_user_by_id(user_id)
        if user is None:
            raise UserDoesNotExist(f"User '{user_id}' does not exist!")
        log.info("Verified user exists!")
        return user

    @abstractmethod
    def execute(self, event: dict, session: Optional[Session]) -> Response:
        """
        Executes the core action implemented by the API method.

        This abstract method serves as a contract for subclasses to define the logic for
        processing API requests. Each subclass implements specific business logic while
        following a consistent interface pattern.

        Args:
            event: The API Gateway Lambda event dictionary containing request data
                   including headers, body, path parameters, and query parameters.
            session: Authentication session context. None for unauthenticated endpoints,
                    populated with user and session data for authenticated endpoints.

        Returns:
            Response object with status code, headers, and serialized body data.

        Raises:
            NotImplementedError: This method must be implemented in a subclass.
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
    def get_query_field(event: dict, field: str) -> Optional[str]:
        if (
            event.get("queryStringParameters") is None
            or field not in event["queryStringParameters"]
            or event["queryStringParameters"][field] is None
        ):
            return None
        return event["queryStringParameters"][field]
