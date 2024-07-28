from dataclasses import dataclass
from datetime import datetime
from typing import List

from polygon import RESTClient
from polygon.rest.models.aggs import Agg
from src.environment import Domain
from src.polygon.models import StockPrice
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class PolygonClient:
    """
    Polygon Client (https://polygon.io/)
    """

    MAX_AGGREGATE_DATA_LIMIT = 50000

    api_key: str
    client: RESTClient = None

    def __post_init__(self) -> None:
        log.debug(f"Creating {Domain.PRODUCTION.value} Polygon client")
        self.client = RESTClient(api_key=self.api_key)

    def get_prices(
        self, symbol: str, start_date: datetime, end_date: datetime
    ) -> List[StockPrice]:
        log.info(
            f"Getting aggregate data for '{symbol}' from '{start_date}' to '{end_date}'"
        )

        if start_date >= end_date:
            raise ValueError(
                f"start date '{start_date}' is after end date '{end_date}'!"
            )

        prices = []
        for agg in self.client.list_aggs(
            ticker=symbol,
            multiplier=1,
            timespan="hour",
            from_=PolygonClient._convert_date_to_string(start_date),
            to=PolygonClient._convert_date_to_string(end_date),
            limit=PolygonClient.MAX_AGGREGATE_DATA_LIMIT,
        ):
            prices.append(PolygonClient._convert_agg_to_stock_price(symbol, agg))

        log.info(
            f"Successfully returned {len(prices)} prices for '{symbol}' from '{start_date}' to '{end_date}'"
        )

        return prices

    @staticmethod
    def _convert_date_to_string(date: datetime) -> str:
        return datetime.strftime(date, "%Y-%m-%d")

    @staticmethod
    def _convert_agg_to_stock_price(symbol: str, agg: Agg) -> StockPrice:
        return StockPrice(
            symbol=symbol,
            price=agg.open,
            timestamp=datetime.fromtimestamp(agg.timestamp / 1000),
        )
