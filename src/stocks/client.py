from dataclasses import dataclass
from datetime import datetime
from typing import Dict

from src.database.userstocks.models import UserStock
from src.stocks.models import Portfolio
from src.stocks.polygon.client import PolygonClient
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class WalterStocksAPI:

    client: PolygonClient

    def __post_init__(self) -> None:
        log.debug("Creating WalterStocksAPI")

    def get_portfolio(
        self, stocks: Dict[str, UserStock], start_date: datetime, end_date: datetime
    ) -> Portfolio:
        prices = self.client.batch_get_prices(stocks, start_date, end_date)
        news = self.client.batch_get_news(stocks, start_date)
        return Portfolio(stocks, prices, news)

    def does_stock_exist(self, symbol: str) -> bool:
        return self.client.get_stock(symbol) is not None
