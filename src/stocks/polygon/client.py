from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict

from polygon import RESTClient
from polygon.rest.models.aggs import Agg

from src.database.userstocks.models import UserStock
from src.environment import Domain
from src.stocks.polygon.models import StockPrice, StockPrices
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class PolygonClient:
    """
    Polygon Client (https://polygon.io/)

    The
    """

    MAX_AGGREGATE_DATA_LIMIT = 50000

    api_key: str

    client: RESTClient = None

    def __post_init__(self) -> None:
        log.debug(f"Creating {Domain.PRODUCTION.value} Polygon client")
        self.client = RESTClient(api_key=self.api_key)

    def batch_get_prices(
        self, stocks: List[UserStock], start_date: datetime, end_date: datetime
    ) -> Dict[str, StockPrices]:
        prices = {}
        for stock in stocks:
            prices[stock.stock_symbol] = self.get_prices(stock, start_date, end_date)
        return prices

    def get_prices(
        self, stock: UserStock, start_date: datetime, end_date: datetime
    ) -> StockPrices:
        log.info(
            f"Getting aggregate data for '{stock.stock_symbol}' from '{start_date}' to '{end_date}'"
        )

        if start_date >= end_date:
            raise ValueError(
                f"start date '{start_date}' is after end date '{end_date}'!"
            )

        prices = []
        for agg in self.client.list_aggs(
            ticker=stock.stock_symbol,
            multiplier=1,
            timespan="hour",
            from_=PolygonClient._convert_date_to_string(start_date),
            to=PolygonClient._convert_date_to_string(end_date),
            limit=PolygonClient.MAX_AGGREGATE_DATA_LIMIT,
        ):
            prices.append(
                PolygonClient._convert_agg_to_stock_price(stock.stock_symbol, agg)
            )

        log.info(f"Successfully returned {len(prices)} prices")

        return StockPrices(prices)

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
