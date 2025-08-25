import json
from dataclasses import dataclass
from typing import Dict, List, Union

from datadog_lambda.metric import lambda_metric

from src.environment import Domain
from src.utils.log import Logger

LOG = Logger(__name__).get_logger()


@dataclass
class DatadogMetricsClient:
    """Datadog Metrics Client"""

    domain: Domain

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
        tags = self._merge_tags(tags)
        LOG.debug(
            f"Tagging metric with the following tags: {json.dumps(tags, indent=4)}"
        )
        lambda_metric(metric_name, metric_value_float, tags=tags)

    def _merge_tags(self, tags: Dict[str, str] = None) -> List[str]:
        merged_tags = {
            "domain": self.domain.value,
        }

        if tags:
            # create copy to avoid modifying caller's dict
            tags_copy = tags.copy()

            if "domain" in tags_copy:
                LOG.warning(
                    "Domain tag cannot be overridden! Ignoring provided domain tag..."
                )
                del tags_copy["domain"]

            merged_tags.update(tags_copy)

        # convert tags dictionary to datadog expected list of key:value strings
        return [f"{key}:{value}" for key, value in merged_tags.items()]
