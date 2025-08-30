from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from src.environment import Domain
from src.metrics.client import DatadogMetricsClient
from src.utils.log import Logger

log = Logger(__name__).get_logger()


class WorkflowStatus(Enum):
    """Workflow Status"""

    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"

    @classmethod
    def from_string(cls, status: str):
        for status_enum in cls:
            if status_enum.value.lower() == status.lower():
                return status_enum
        raise ValueError(f"{status} is not a valid status!")


@dataclass
class WorkflowResponse:
    """Workflow Response"""

    name: str
    status: WorkflowStatus
    message: str
    data: Optional[dict] = None

    def to_json(self) -> dict:
        response = {
            "Service": "WalterBackend",
            "Workflow": self.name,
            "Status": self.status.value,
            "Message": self.message,
        }

        # add optional data field to response
        if self.data:
            response["Data"] = self.data

        return response


class Workflow(ABC):
    """Workflow Base Class"""

    SUCCESS_COUNT_METRIC = "workflow.success"
    FAILURE_COUNT_METRIC = "workflow.failure"
    DURATION_MS_METRIC = "workflow.duration_ms"

    def __init__(
        self, name: str, domain: Domain, metrics: DatadogMetricsClient
    ) -> None:
        self.name = name
        self.domain = domain
        self.metrics = metrics

    def invoke(self, event: dict, emit_metrics: bool = True) -> WorkflowResponse:
        log.info(f"Invoking '{self.name}' workflow!")

        # start timer to get workflow duration
        start = datetime.now(timezone.utc)

        # assume workflow failure until workflow execution succeeds
        success = False
        try:
            response = self.execute(event, emit_metrics)
            success = True
        except Exception as e:
            log.error("Error occurred during workflow execution!", exc_info=True)
            response = WorkflowResponse(self.name, WorkflowStatus.FAILURE, str(e))
        finally:
            end = datetime.now(timezone.utc)
            duration_ms = int((end - start).total_seconds() * 1000)

            # emit workflow metrics if enabled
            if emit_metrics:
                self._emit_metrics(success, duration_ms)
            else:
                log.info(f"Not emitting metrics for '{self.name}' workflow!")

        return response

    @abstractmethod
    def execute(self, event: dict, emit_metrics: bool) -> WorkflowResponse:
        pass

    def _emit_metrics(self, success: bool, duration_ms: int) -> None:
        tags = self._get_metric_tags()
        self.metrics.emit_metric(self.SUCCESS_COUNT_METRIC, success, tags)
        self.metrics.emit_metric(self.FAILURE_COUNT_METRIC, not success, tags)
        self.metrics.emit_metric(self.DURATION_MS_METRIC, duration_ms, tags)

    def _get_metric_tags(self) -> dict:
        return {"workflow": self.name, "domain": self.domain}
