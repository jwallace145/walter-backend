from dataclasses import dataclass
from datetime import datetime
from typing import Dict

from src.database.stocks.models import Stock
from src.database.userstocks.models import UserStock
from src.stocks.models import Portfolio
from src.stocks.polygon.client import PolygonClient
from src.stocks.polygon.models import StockPrices
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class WalterStocksAPI:

    client: PolygonClient

    def __post_init__(self) -> None:
        log.debug("Creating WalterStocksAPI")

    def get_portfolio(
        self,
        user_stocks: Dict[str, UserStock],
        stocks: Dict[str, Stock],
        start_date: datetime,
        end_date: datetime,
    ) -> Portfolio:
        prices = self.client.batch_get_prices(user_stocks, start_date, end_date)
        news = self.client.batch_get_news(user_stocks, start_date)
        return Portfolio(stocks, user_stocks, prices, news)

    def get_stock(self, symbol: str) -> Stock | None:
        return self.client.get_stock(symbol)

    def get_prices(self, stock: str) -> StockPrices:
        return self.client.get_stock_prices(stock)
