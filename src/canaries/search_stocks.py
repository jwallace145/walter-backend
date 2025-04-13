from dataclasses import dataclass

import requests
from requests import Response

from src.canaries.common.canary import BaseCanary
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class SearchStocksCanary(BaseCanary):
    """
    WalterCanary: SearchStocksCanary

    This canary calls the SearchStocks API to search for stocks
    that are similar to the given identifier. This canary ensures
    users can query stocks by ticker symbol.
    """

    CANARY_NAME = "SearchStocksCanary"
    API_URL = "https://084slq55lk.execute-api.us-east-1.amazonaws.com/dev/stocks/search"
    STOCK_SYMBOL = "MET"

    def __init__(self) -> None:
        super().__init__(SearchStocksCanary.CANARY_NAME, SearchStocksCanary.API_URL)

    def call_api(self) -> Response:
        return requests.get(
            SearchStocksCanary.API_URL,
            params={"symbol": SearchStocksCanary.STOCK_SYMBOL},
        )
