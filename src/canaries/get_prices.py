from dataclasses import dataclass

import requests

from src.api.common.models import Status
from src.canaries.common.models import CanaryResponse
from src.utils.log import Logger
import datetime as dt

log = Logger(__name__).get_logger()


@dataclass
class GetPricesCanary:
    """
    WalterCanary: GetPricesCanary

    This canary calls the GetPrices API to get pricing data
    for the given stock. This ensures that users are able to
    query stock market pricing data successfully.
    """

    CANARY_NAME = "GetPricesCanary"
    API_URL = "https://084slq55lk.execute-api.us-east-1.amazonaws.com/dev/prices"
    STOCK_SYMBOL = "META"

    def __post_init__(self) -> None:
        log.debug(f"Initializing {GetPricesCanary.CANARY_NAME}")

    def invoke(self) -> dict:
        log.info(f"Invoked '{GetPricesCanary.CANARY_NAME}'!")

        start = dt.datetime.now(dt.UTC)

        response = requests.get(
            GetPricesCanary.API_URL, params={"stock": GetPricesCanary.STOCK_SYMBOL}
        )

        end = dt.datetime.now(dt.UTC)

        log.info(
            f"API Response - Status Code: {response.status_code}"
        )

        return CanaryResponse(
            canary_name=GetPricesCanary.CANARY_NAME,
            status=Status.SUCCESS if response.status_code == 200 else Status.FAILURE,
            response_time_millis=(end - start).total_seconds() * 1000,
        ).to_json()
