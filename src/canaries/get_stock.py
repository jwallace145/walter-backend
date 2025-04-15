from dataclasses import dataclass

import requests
from requests import Response

from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.canaries.common.canary import BaseCanary
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class GetStockCanary(BaseCanary):
    """
    WalterCanary: GetStockCanary

    This canary calls the GetStock API to get the stock
    information stored in WalterDB. This canary validates
    user access to stock information in the database.
    """

    CANARY_NAME = "GetStockCanary"
    API_URL = "https://084slq55lk.execute-api.us-east-1.amazonaws.com/dev/stocks"
    STOCK_SYMBOL = "NFLX"

    def __init__(self, metrics: WalterCloudWatchClient) -> None:
        super().__init__(GetStockCanary.CANARY_NAME, GetStockCanary.API_URL, metrics)

    def call_api(self) -> Response:
        return requests.get(
            GetStockCanary.API_URL, params={"symbol": GetStockCanary.STOCK_SYMBOL}
        )
