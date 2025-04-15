from dataclasses import dataclass

import requests
from requests import Response

from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.canaries.common.canary import BaseCanary
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class GetNewsSummaryCanary(BaseCanary):
    """
    WalterCanary: GetNewsSummaryCanary

    This canary calls the GetNewsSummary API to get the
    latest news summary for the given stock. This canary
    validates Walter's news summarization and the ability
    to get the latest summaries.
    """

    CANARY_NAME = "GetNewsSummaryCanary"
    API_URL = "https://084slq55lk.execute-api.us-east-1.amazonaws.com/dev/news"
    STOCK_SYMBOL = "META"

    def __init__(self, metrics: WalterCloudWatchClient) -> None:
        super().__init__(
            GetNewsSummaryCanary.CANARY_NAME, GetNewsSummaryCanary.API_URL, metrics
        )

    def call_api(self) -> Response:
        return requests.get(
            GetNewsSummaryCanary.API_URL,
            params={"symbol": GetNewsSummaryCanary.STOCK_SYMBOL},
        )
