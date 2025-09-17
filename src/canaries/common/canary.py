import datetime as dt
import json
import time
from abc import ABC, abstractmethod
from typing import List, Optional, Union

from requests import Response

from src.api.common.exceptions import SessionDoesNotExist
from src.api.common.models import Status
from src.auth.authenticator import WalterAuthenticator
from src.auth.models import Tokens
from src.canaries.common.exceptions import CanaryFailure
from src.canaries.common.metrics import (
    METRICS_FAILURE_COUNT,
    METRICS_RESPONSE_TIME_MILLISECONDS,
    METRICS_SUCCESS_COUNT,
)
from src.canaries.common.models import CanaryResponse
from src.config import CONFIG
from src.database.client import WalterDB
from src.database.sessions.models import Session
from src.database.users.models import User
from src.metrics.client import DatadogMetricsClient
from src.utils.log import Logger

log = Logger(__name__).get_logger()


class BaseCanary(ABC):
    """
    Base class for API health monitoring canaries.

    Canaries run on scheduled intervals to test API endpoints and emit metrics
    for monitoring dashboards. Each canary measures response time and success/failure
    rates to track API performance and availability.

    Key responsibilities:
    - Execute API calls with timing measurement
    - Emit success/failure and response time metrics to Datadog
    - Handle errors gracefully and log detailed information
    - Return standardized canary execution results
    """

    CANARY_ENDPOINT = CONFIG.canaries.endpoint
    CANARY_USER_EMAIL = CONFIG.canaries.user_email
    CANARY_USER_PASSWORD = CONFIG.canaries.user_password

    def __init__(
        self,
        api_name: str,
        api_url: str,
        authenticator: WalterAuthenticator,
        db: WalterDB,
        metrics: DatadogMetricsClient,
    ) -> None:
        self.api_name = api_name
        self.api_url = api_url
        self.authenticator = authenticator
        self.db = db
        self.metrics = metrics

    def invoke(self, emit_metrics: bool = True) -> dict:
        """Execute the canary test and emit metrics."""
        log.info(f"Invoked '{self.api_name}' canary!")

        # start timer to get api response time
        start = dt.datetime.now(dt.UTC)

        # assume api failure until api response status is confirmed as success
        api_status = Status.FAILURE
        try:

            # get tokens if api is authenticated
            user = None
            tokens = None
            if self.is_authenticated():
                log.info(f"'{self.api_name}' canary requires authentication!")
                user = self.db.get_user_by_email(self.CANARY_USER_EMAIL)
                tokens = self._start_session(user)

            log.info(f"Calling API at '{self.api_url}'")
            api_response = self.call_api(tokens)
            api_status_code = api_response.status_code
            api_response_json = api_response.json()
            api_status = Status.from_string(api_response_json.get("Status", "Failure"))
            log.info(
                f"API Response - Status Code: {api_status_code} Status: {api_status.value}"
            )
            log.debug(f"API Response - JSON: {json.dumps(api_response_json, indent=4)}")
            self.validate(api_response_json)

            # end session if api is authenticated
            if self.is_authenticated():
                log.info(f"'{self.api_name}' canary ending authenticated session!")
                self._end_session(user, tokens)

        except Exception:
            log.error(
                f"Unexpected exception occurred invoking '{self.api_name}'!",
                exc_info=True,
            )
            api_status = Status.FAILURE
        finally:
            # get api response time
            end = dt.datetime.now(dt.UTC)
            response_time_millis = (end - start).total_seconds() * 1000

            # check api status
            success = api_status == Status.SUCCESS

            # emit canary metrics if enabled
            if emit_metrics:
                self._emit_metrics(success, response_time_millis)
            else:
                log.info(f"Emitting metrics for '{self.api_name}' canary is disabled!")

            # perform any clean up actions to ensure no dangling resources
            self.clean_up()

            return CanaryResponse(
                api_name=self.api_name,
                status=Status.SUCCESS if success else Status.FAILURE,
                response_time_millis=(end - start).total_seconds() * 1000,
            ).to_json()

    def _start_session(self, user: User) -> Tokens:
        # ensure canary user exists before starting session for authenticated api
        if user is None:
            log.error(f"User with email '{self.CANARY_USER_EMAIL}' does not exist!")
            raise Exception("Canary user does not exist!")

        log.info(
            f"Starting authenticated session for '{self.api_name}' canary for user '{user.user_id}'..."
        )
        tokens = self.authenticator.generate_tokens(user.user_id)
        self._create_session(user, tokens)
        return tokens

    def _create_session(self, user: User, tokens: Tokens) -> Session:
        log.info(
            f"Creating new session for user '{user.user_id}' with session ID '{tokens.jti}'"
        )

        # constant client IP and device for canaries
        client_ip = "WalterBackendCanary"
        client_device = "WalterBackendCanary"

        # create session in db
        session = self.db.create_session(
            user.user_id, tokens.jti, client_ip, client_device
        )

        log.info(
            f"Created new session for user '{user.user_id}' with token ID '{tokens.jti}'"
        )

        return session

    def _end_session(self, user: User, tokens: Tokens) -> None:
        log.info(
            f"Ending authenticated session for '{self.api_name}' canary for session '{tokens.jti}'"
        )
        session = self.db.get_session(user.user_id, tokens.jti)
        if not session:
            raise SessionDoesNotExist(
                f"Session '{tokens.jti}' does not exist for user '{user.user_id}'!"
            )
        now = dt.datetime.now(dt.UTC)
        session.revoked = True
        session.session_end = now
        session.ttl = int(
            time.time()
        )  # immediately expire canary session to reduce num db entries
        self.db.update_session(session)
        log.info(
            f"Ended authenticated session for '{self.api_name}' canary for session '{tokens.jti}'"
        )

    def validate(self, response: dict) -> None:
        """Validate the API response."""
        log.info(f"Validating '{self.api_name}' API response status...")

        if response.get("Status") != "Success":
            log.error(f"API call failure! Response: {json.dumps(response, indent=4)}")
            raise CanaryFailure("API call failure!")

        log.info(f"Validated '{self.api_name}' API response status!")

        log.info(f"Validating '{self.api_name}' API response cookies...")
        self.validate_cookies(response)
        log.info(f"Validated '{self.api_name}' API response cookies!")

        log.info(f"Validating '{self.api_name}' API response data...")
        self.validate_data(response)
        log.info(f"Validated '{self.api_name}' API response data!")

        log.info(f"'{self.api_name}' API response validated successfully!")

    def _validate_required_response_cookies(
        self, response: dict, cookies: List[str]
    ) -> None:
        """Validate required cookies in the API response."""
        response_cookies = set()
        for response_cookie in response.get("Set-Cookies", {}):
            response_cookies.add(response_cookie.split(";")[0].split("=")[0])

        for cookie in cookies:
            if cookie not in response_cookies:
                raise CanaryFailure(
                    f"Required cookie '{cookie}' not found in response!"
                )

        if len(response_cookies) != len(cookies):
            raise CanaryFailure("API response contains additional unexpected cookies!")

    def _validate_required_response_data_fields(
        self, response: dict, required_fields: List[str]
    ) -> None:
        """Validate required fields in the API response data."""
        response_data = response.get("Data", {})

        for field in required_fields:
            if field not in response_data:
                raise CanaryFailure(f"Required field '{field}' not found in response!")

        if len(response_data) != len(required_fields):
            raise CanaryFailure("API response data contains additional fields!")

    def _emit_metrics(self, success: bool, response_time_millis: float) -> None:
        """Send success, failure, and response time metrics to Datadog."""
        log.info(f"Emitting metrics for '{self.api_name}' canary...")
        self.metrics.emit_metric(
            f"canary.{METRICS_SUCCESS_COUNT}", success, tags={"api": self.api_name}
        )
        self.metrics.emit_metric(
            f"canary.{METRICS_FAILURE_COUNT}", not success, tags={"api": self.api_name}
        )
        self.metrics.emit_metric(
            f"canary.{METRICS_RESPONSE_TIME_MILLISECONDS}",
            response_time_millis,
            tags={"api": self.api_name},
        )

    @abstractmethod
    def is_authenticated(self) -> bool:
        """
        Return True if the canary tests an authenticated endpoint.

        Override this method to indicate whether the API endpoint requires
        authentication. If True, the canary should handle obtaining and
        using access tokens for API calls.
        """
        pass

    @abstractmethod
    def call_api(self, token: Optional[Tokens] = None) -> Response:
        """
        Make the API call to test endpoint health.

        Override this method to implement the specific API request
        that this canary will monitor. Should return the HTTP response
        for status and timing analysis.
        """
        pass

    @abstractmethod
    def validate_cookies(self, response: dict) -> None:
        """
        Validate the API response cookies specific to the canary.

        Override this method to implement the specific validation logic
        for verifying the presence of cookies in the API response. Few
        APIs return cookies so this method will be not implemented
        for a large majority of canaries.

        Args:
            response: The API response object.

        Throws:
            CanaryException: If the response cookies are missing or invalid.
        """
        pass

    @abstractmethod
    def validate_data(self, response: dict) -> None:
        """
        Validate the API response data specific to the canary.

        Override this method to implement the specific validation logic
        for the API response data. Should raise an exception if the response
        data is invalid.

        Raises:
            CanaryFailure: If the response data is invalid.
        """
        pass

    @abstractmethod
    def clean_up(self) -> None:
        """
        Perform any clean up actions to ensure no dangling resources.
        """
        pass

    @staticmethod
    def validate_response_data(response: dict) -> dict:
        log.debug("Validating data in response...")
        if response.get("Data", None) is None:
            raise CanaryFailure("Missing data in response!")
        log.debug("Validated data in response!")
        return response["Data"]

    @staticmethod
    def validate_required_field(
        fields: dict,
        field_name: str,
        field_value: Optional[Union[str, int, float]] = None,
    ) -> None:
        log.debug(f"Validating required field '{field_name}' in dictionary...")
        if fields.get(field_name, None) is None:
            raise CanaryFailure(f"Missing required field '{field_name}' in dictionary!")
        if field_value is not None:
            if fields[field_name] != field_value:
                raise CanaryFailure(
                    f"Unexpected value for field '{field_name}' in dictionary: '{fields[field_name]}'"
                )
        log.debug(f"Validated required field '{field_name}' in dictionary!")
