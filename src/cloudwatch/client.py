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

    METRIC_NAME_NUMBER_OF_EMAILS_SENT = "NumberOfEmailsSent-{domain}"
    METRIC_NAME_NUMBER_OF_STOCKS_ANALYZED = "NumberOfStocksAnalyzed-{domain}"
    METRIC_NAME_NUMBER_OF_SUBSCRIBED_USERS = "NumberOfSubscribedUsers-{domain}"

    client: CloudWatchClient
    domain: Domain

    metric_name_number_of_emails_sent: str = None
    metric_name_number_of_stocks_analyzed: str = None
    metric_name_number_of_subscribed_users: str = None

    def __post_init__(self) -> None:
        log.debug(
            f"Creating {self.domain.value} CloudWatch client in region '{self.client.meta.region_name}'"
        )
        self.metric_name_number_of_emails_sent = (
            CloudWatchClient._get_number_of_emails_sent_metric_name(self.domain)
        )
        self.metric_name_number_of_stocks_analyzed = (
            CloudWatchClient._get_number_of_stocks_analyzed_metric_name(self.domain)
        )
        self.metric_name_number_of_subscribed_users = (
            CloudWatchClient._get_number_of_subscribed_users_metric_name(self.domain)
        )

    def emit_metric_number_of_emails_sent(self, num_emails: int) -> None:
        self.client.put_metric_data(
            MetricName=self.metric_name_number_of_emails_sent, Value=num_emails
        )

    def emit_metric_number_of_stocks_analyzed(self, num_stocks: int) -> None:
        self.client.put_metric_data(
            MetricName=self.metric_name_number_of_stocks_analyzed, Value=num_stocks
        )

    def emit_metric_number_of_subscribed_users(self, num_users: int) -> None:
        self.client.put_metric_data(
            MetricName=self.metric_name_number_of_subscribed_users, Value=num_users
        )

    @staticmethod
    def _get_number_of_emails_sent_metric_name(domain: Domain) -> str:
        return CloudWatchClient.METRIC_NAME_NUMBER_OF_EMAILS_SENT.format(
            domain=domain.value
        )

    @staticmethod
    def _get_number_of_stocks_analyzed_metric_name(domain: Domain) -> str:
        return CloudWatchClient.METRIC_NAME_NUMBER_OF_STOCKS_ANALYZED.format(
            domain=domain.value
        )

    @staticmethod
    def _get_number_of_subscribed_users_metric_name(domain: Domain) -> str:
        return CloudWatchClient.METRIC_NAME_NUMBER_OF_SUBSCRIBED_USERS.format(
            domain=domain.value
        )
