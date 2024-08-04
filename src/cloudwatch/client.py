from dataclasses import dataclass

from mypy_boto3_cloudwatch import CloudWatchClient
from src.environment import Domain
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class CloudWatchClient:
    """
    WalterAI CloudWatch Client

    Metrics:
        - The number of emails sent
        - The number of stocks analyzed
        - The number of subscribed users
    """

    METRIC_NAMESPACE = "WalterAIBackend/{domain}"
    METRIC_NAME_NUMBER_OF_EMAILS_SENT = "NumberOfEmailsSent"
    METRIC_NAME_NUMBER_OF_STOCKS_ANALYZED = "NumberOfStocksAnalyzed"
    METRIC_NAME_NUMBER_OF_SUBSCRIBED_USERS = "NumberOfSubscribedUsers"

    client: CloudWatchClient
    domain: Domain

    metric_namespace: str = None

    def __post_init__(self) -> None:
        log.debug(
            f"Creating {self.domain.value} CloudWatch client in region '{self.client.meta.region_name}'"
        )
        self.metric_namespace = CloudWatchClient._get_metric_namespace(self.domain)

    def emit_metric_number_of_emails_sent(self, num_emails: int) -> None:
        self.client.put_metric_data(
            Namespace=self.metric_namespace,
            MetricData=[
                {
                    "MetricName": CloudWatchClient.METRIC_NAME_NUMBER_OF_EMAILS_SENT,
                    "Unit": "Count",
                    "Value": num_emails,
                }
            ],
        )

    def emit_metric_number_of_stocks_analyzed(self, num_stocks: int) -> None:
        self.client.put_metric_data(
            Namespace=self.metric_namespace,
            MetricData=[
                {
                    "MetricName": CloudWatchClient.METRIC_NAME_NUMBER_OF_STOCKS_ANALYZED,
                    "Unit": "Count",
                    "Value": num_stocks,
                }
            ],
        )

    def emit_metric_number_of_subscribed_users(self, num_users: int) -> None:
        self.client.put_metric_data(
            Namespace=self.metric_namespace,
            MetricData=[
                {
                    "MetricName": CloudWatchClient.METRIC_NAME_NUMBER_OF_SUBSCRIBED_USERS,
                    "Unit": "Count",
                    "Value": num_users,
                }
            ],
        )

    @staticmethod
    def _get_metric_namespace(domain: Domain) -> str:
        return CloudWatchClient.METRIC_NAMESPACE.format(domain=domain.value)
