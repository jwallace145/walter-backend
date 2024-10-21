from dataclasses import dataclass

from mypy_boto3_cloudwatch import CloudWatchClient
from src.environment import Domain
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class WalterCloudWatchClient:
    """
    WalterBackend Cloud Watch Client
    """

    METRIC_NAMESPACE = "WalterBackend/{domain}"

    client: CloudWatchClient
    domain: Domain

    metric_namespace: str = None

    def __post_init__(self) -> None:
        log.debug(
            f"Creating '{self.domain.value}' CloudWatch client in region '{self.client.meta.region_name}'"
        )
        self.metric_namespace = WalterCloudWatchClient._get_metric_namespace(
            self.domain
        )

    def emit_metric(self, metric_name: str, count: int) -> None:
        self.client.put_metric_data(
            Namespace=self.metric_namespace,
            MetricData=[
                {
                    "MetricName": metric_name,
                    "Unit": "Count",
                    "Value": count,
                }
            ],
        )

    @staticmethod
    def _get_metric_namespace(domain: Domain) -> str:
        return WalterCloudWatchClient.METRIC_NAMESPACE.format(domain=domain.value)
