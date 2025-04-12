from dataclasses import dataclass

import requests

from src.api.common.models import Status
from src.canaries.common.models import CanaryResponse
from src.utils.log import Logger

import datetime as dt

log = Logger(__name__).get_logger()


@dataclass
class GetStockCanary:
    """
    WalterCanary: GetStockCanary

    This canary calls the GetStock API to get the stock
    information stored in WalterDB. This canary validates
    user access to stock information in the database.
    """

    CANARY_NAME = "GetStockCanary"
    API_URL = "https://084slq55lk.execute-api.us-east-1.amazonaws.com/dev/stocks"
    STOCK_SYMBOL = "NFLX"

    def __post_init__(self) -> None:
        log.debug(f"Initializing {GetStockCanary.CANARY_NAME}")

    def invoke(self) -> dict:
        log.info(f"Invoked '{GetStockCanary.CANARY_NAME}'!")

        start = dt.datetime.now(dt.UTC)

        response = requests.get(
            GetStockCanary.API_URL, params={"symbol": GetStockCanary.STOCK_SYMBOL}
        )

        end = dt.datetime.now(dt.UTC)

        log.info(f"API Response - Status Code: {response.status_code}")

        return CanaryResponse(
            canary_name=GetStockCanary.CANARY_NAME,
            status=Status.SUCCESS if response.status_code == 200 else Status.FAILURE,
            response_time_millis=(end - start).total_seconds() * 1000,
        ).to_json()
