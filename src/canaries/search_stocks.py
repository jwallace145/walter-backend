from dataclasses import dataclass

import requests

from src.api.common.models import Status
from src.canaries.common.models import CanaryResponse
from src.utils.log import Logger

import datetime as dt

log = Logger(__name__).get_logger()


@dataclass
class SearchStocksCanary:
    """
    WalterCanary: SearchStocksCanary

    This canary calls the SearchStocks API to search for stocks
    that are similar to the given identifier. This canary ensures
    users can query stocks by ticker symbol.
    """

    CANARY_NAME = "SearchStocksCanary"
    API_URL = "https://084slq55lk.execute-api.us-east-1.amazonaws.com/dev/stocks/search"
    STOCK_SYMBOL = "MET"

    def __post_init__(self) -> None:
        log.debug(f"Initializing {SearchStocksCanary.CANARY_NAME}")

    def invoke(self) -> dict:
        log.info(f"Invoked '{SearchStocksCanary.CANARY_NAME}'!")

        start = dt.datetime.now(dt.UTC)

        response = requests.get(
            SearchStocksCanary.API_URL,
            params={"symbol": SearchStocksCanary.STOCK_SYMBOL},
        )

        end = dt.datetime.now(dt.UTC)

        log.info(f"API Response - Status Code: {response.status_code}")

        return CanaryResponse(
            canary_name=SearchStocksCanary.CANARY_NAME,
            status=Status.SUCCESS if response.status_code == 200 else Status.FAILURE,
            response_time_millis=(end - start).total_seconds() * 1000,
        ).to_json()
