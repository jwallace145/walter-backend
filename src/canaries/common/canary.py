import datetime as dt
import json
from abc import ABC, abstractmethod

from requests import Response

from src.api.common.models import Status
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.canaries.common.models import CanaryResponse
from src.utils.log import Logger

log = Logger(__name__).get_logger()

###########
# METRICS #
###########

METRICS_SUCCESS_COUNT = "SuccessCount"
"""(str): The name of the canary metric for successful API invocation count."""

METRICS_FAILURE_COUNT = "FailureCount"
"""(str): The name of the canary metric for failed API invocation count."""

METRICS_RESPONSE_TIME_MILLISECONDS = "ResponseTimeMilliseconds"
"""(str): The name of the canary metric for API response time in milliseconds."""

###############
# BASE CANARY #
###############


class BaseCanary(ABC):
    """
    WalterCanary: BaseCanary

    This class contains the undifferentiated logic for a
    Walter canary. The purpose of a canary is to ensure
    all the various APIs are healthy and emit helpful
    operational metrics for the WalterAPI dashboard.

    Canaries are invoked on a cron schedule so the metrics
    produced by the canaries are emitted at regular intervals
    and are therefore instrumental for the dashboard.

    The greatest use case of a canary so far is emitting API
    response time metrics to quantify the user experience.
    This metric is a key performance indicator in the
    WalterAPI dashboard.
    """

    def __init__(
        self, canary_name: str, api_url: str, metrics: WalterCloudWatchClient
    ) -> None:
        self.canary_name = canary_name
        self.api_url = api_url
        self.metrics = metrics

    def invoke(self) -> dict:
        log.info(f"Invoked '{self.canary_name}'!")

        # start timer to get api response time
        start = dt.datetime.now(dt.UTC)

        # assume api failure until api response status is confirmed as success
        api_status = Status.FAILURE
        try:
            api_response = self.call_api()
            api_status_code = api_response.status_code
            api_response_json = api_response.json()
            api_status = Status.from_string(
                api_response_json.get("Status", "Failure")
            )
            log.info(
                f"API Response - Status Code: {api_status_code} Status: {api_status.value}"
            )
            log.debug(f"API Response - JSON: {json.dumps(api_response_json, indent=4)}")
        except Exception:
            log.error(
                f"Unexpected exception occurred invoking '{self.canary_name}'!",
                exc_info=True,
            )
        finally:
            # get api response time
            end = dt.datetime.now(dt.UTC)
            response_time_millis = (end - start).total_seconds() * 1000
            success = api_status == Status.SUCCESS
            self._emit_metrics(success, response_time_millis)
            return CanaryResponse(
                canary_name=self.canary_name,
                status=Status.SUCCESS if success else Status.FAILURE,
                response_time_millis=(end - start).total_seconds() * 1000,
            ).to_json()

    def _emit_metrics(self, success: bool, response_time_millis: float) -> None:
        log.info(f"Emitting metrics for '{self.canary_name}'...")
        success_count_metric_name = self._get_success_count_metric_name()
        self.metrics.emit_metric(success_count_metric_name, success)
        failure_count_metric_name = self._get_failure_count_metric_name()
        self.metrics.emit_metric(failure_count_metric_name, not success)
        response_time_metric_name = self._get_response_time_metric_name()
        self.metrics.emit_metric(response_time_metric_name, response_time_millis)

    def _get_success_count_metric_name(self) -> str:
        return f"{self.canary_name}.{METRICS_SUCCESS_COUNT}"

    def _get_failure_count_metric_name(self) -> str:
        return f"{self.canary_name}.{METRICS_FAILURE_COUNT}"

    def _get_response_time_metric_name(self) -> str:
        return f"{self.canary_name}.{METRICS_RESPONSE_TIME_MILLISECONDS}"

    @abstractmethod
    def call_api(self) -> Response:
        pass
