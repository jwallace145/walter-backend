from dataclasses import dataclass

import requests

from src.api.common.models import Status
from src.canaries.common.models import CanaryResponse
from src.utils.log import Logger

import datetime as dt

log = Logger(__name__).get_logger()


@dataclass
class GetNewsSummaryCanary:
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

    def __post_init__(self) -> None:
        log.debug(f"Initializing {GetNewsSummaryCanary.CANARY_NAME}")

    def invoke(self) -> dict:
        log.info(f"Invoked '{GetNewsSummaryCanary.CANARY_NAME}'!")

        start = dt.datetime.now(dt.UTC)

        response = requests.get(
            GetNewsSummaryCanary.API_URL,
            params={"symbol": GetNewsSummaryCanary.STOCK_SYMBOL},
        )

        end = dt.datetime.now(dt.UTC)

        log.info(f"API Response - Status Code: {response.status_code}")

        return CanaryResponse(
            canary_name=GetNewsSummaryCanary.CANARY_NAME,
            status=Status.SUCCESS if response.status_code == 200 else Status.FAILURE,
            response_time_millis=(end - start).total_seconds() * 1000,
        ).to_json()
