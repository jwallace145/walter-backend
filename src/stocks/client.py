from dataclasses import dataclass
from datetime import datetime, timedelta, UTC
from typing import Dict

from src.database.stocks.models import Stock
from src.database.userstocks.models import UserStock
from src.stocks.models import Portfolio
from src.stocks.polygon.client import PolygonClient
from src.stocks.polygon.models import StockPrices, StockNews, PolygonStock
from src.stocks.yahoo.client import YahooFinanceClient
from src.stocks.yahoo.models import YahooFinanceStock
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class WalterStocksAPI:

    polygon: PolygonClient
    yahoo: YahooFinanceClient

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
        log.info(f"Getting stock '{symbol}' from Yahoo Finance")
        yahoo_finance_stock = self.yahoo.get_stock(symbol)
        if (polygon_stock is None or yahoo_finance_stock is None):
            return None
        return WalterStocksAPI.from_polygon_and_yahoo_finance(
            polygon_stock, yahoo_finance_stock
        )

    def get_news(self, symbol: str) -> StockNews | None:
        return self.polygon.get_news(symbol, datetime.now(UTC) - timedelta(days=7))

    def get_prices(self, stock: str) -> StockPrices:
        return self.polygon.get_stock_prices(stock)

    @staticmethod
    def from_polygon_and_yahoo_finance(
        polygon_stock: PolygonStock, yahoo_finance_stock: YahooFinanceStock
    ) -> Stock:
        return Stock(
            symbol=polygon_stock.symbol,
            company=polygon_stock.company,
            sector=yahoo_finance_stock.sector,
            industry=yahoo_finance_stock.industry,
        )
