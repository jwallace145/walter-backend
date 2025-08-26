import datetime as dt
import json
import time
from abc import ABC, abstractmethod
from typing import List, Optional

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

    CANARY_USER_EMAIL = "canary@walterai.dev"
    CANARY_USER_PASSWORD = "CanaryPassword1234&"

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
            success = api_status == Status.SUCCESS
            if emit_metrics:
                self._emit_metrics(success, response_time_millis)
            else:
                log.info(f"Emitting metrics for '{self.api_name}' canary is disabled!")
            return CanaryResponse(
                api_name=self.api_name,
                status=Status.SUCCESS if success else Status.FAILURE,
                response_time_millis=(end - start).total_seconds() * 1000,
            ).to_json()

    def _start_session(self, user: User) -> Tokens:
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
            raise CanaryFailure("API call failure!")

        log.info(f"Validated '{self.api_name}' API response status!")

        log.info(f"Validating '{self.api_name}' API response data...")
        self.validate_data(response)
        log.info(f"Validated '{self.api_name}' API response data!")

        log.info(f"'{self.api_name}' API response validated successfully!")

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
