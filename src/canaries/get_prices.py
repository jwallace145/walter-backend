from dataclasses import dataclass

import requests
from requests import Response

from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.canaries.common.canary import BaseCanary
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class GetPricesCanary(BaseCanary):
    """
    WalterCanary: GetPricesCanary

    This canary calls the GetPrices API to get pricing data
    for the given stock. This ensures that users are able to
    query stock market pricing data successfully.
    """

    CANARY_NAME = "GetPricesCanary"
    API_URL = "https://084slq55lk.execute-api.us-east-1.amazonaws.com/dev/prices"
    STOCK_SYMBOL = "META"

    def __init__(self, metrics: WalterCloudWatchClient) -> None:
        super().__init__(GetPricesCanary.CANARY_NAME, GetPricesCanary.API_URL, metrics)

    def call_api(self) -> Response:
        return requests.get(
            GetPricesCanary.API_URL, params={"stock": GetPricesCanary.STOCK_SYMBOL}
        )
