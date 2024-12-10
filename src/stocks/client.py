from dataclasses import dataclass
from datetime import datetime, timedelta, UTC
from typing import Dict

from src.database.stocks.models import Stock
from src.database.userstocks.models import UserStock
from src.stocks.models import Portfolio
from src.stocks.polygon.client import PolygonClient
from src.stocks.polygon.models import StockPrices, StockNews
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class WalterStocksAPI:

    polygon: PolygonClient

    def __post_init__(self) -> None:
        log.debug("Creating WalterStocksAPI")

    def get_portfolio(
        self,
        user_stocks: Dict[str, UserStock],
        stocks: Dict[str, Stock],
        start_date: datetime,
        end_date: datetime,
    ) -> Portfolio:
        prices = self.polygon.batch_get_prices(user_stocks, start_date, end_date)
        news = self.polygon.batch_get_news(user_stocks, start_date)
        return Portfolio(stocks, user_stocks, prices, news)

    def get_stock(self, symbol: str) -> Stock | None:
        log.info(f"Getting stock '{symbol}' from Polygon")
        polygon_stock = self.polygon.get_stock(symbol)
        if polygon_stock is None:
            return None
        return Stock(
            symbol=polygon_stock.symbol,
            company=polygon_stock.company,
        )

    def get_news(self, symbol: str) -> StockNews | None:
        return self.polygon.get_news(symbol, datetime.now(UTC) - timedelta(days=7))

    def get_prices(self, stock: str) -> StockPrices:
        return self.polygon.get_stock_prices(stock)
