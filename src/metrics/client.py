import json
from dataclasses import dataclass
from typing import Dict, Union

from datadog_lambda.metric import lambda_metric

from src.utils.log import Logger

LOG = Logger(__name__).get_logger()


@dataclass
class DatadogMetricsClient:
    """Datadog Metrics Client"""

    def __post_init__(self) -> None:
        LOG.debug("Creating Datadog metrics client")

    def emit_metric(
        self,
        metric_name: str,
        metric_value: Union[float, bool],
        tags: Dict[str, str] = None,
    ) -> None:
        """
        Emit a metric to Datadog.

        Args:
            metric_name: The name of the metric.
            metric_value: The value of the metric. Either float or boolean.
            tags: Optional tags to attach to the metric for enhanced filtering.
        """
        # convert boolean to float if needed
        metric_value_float = metric_value
        if isinstance(metric_value, bool):
            metric_value_float = 1.0 if metric_value else 0.0

        LOG.debug(f"Emitting metric '{metric_name}' with value '{metric_value}'")

        # add tags if provided
        if tags:
            LOG.debug(
                f"Tagging metric with the following tags: {json.dumps(tags, indent=4)}"
            )
            lambda_metric(metric_name, metric_value_float, tags=tags)
        else:
            lambda_metric(metric_name, metric_value_float)
