import datetime as dt
from dataclasses import dataclass
from typing import List

from src.stocks.alphavantage.client import AlphaVantageClient
from src.stocks.alphavantage.models import (
    CompanySearch,
    CompanyStatistics,
)
from src.stocks.polygon.client import PolygonClient
from src.stocks.polygon.models import StockPrices
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class WalterStocksAPI:
    """
    WalterStocksAPI
    """

    polygon: PolygonClient
    alpha_vantage: AlphaVantageClient

    def __post_init__(self) -> None:
        log.debug("Creating WalterStocksAPI")

    def search_stock(self, symbol: str) -> List[CompanySearch]:
        log.info(f"Searching for stocks similar to '{symbol}'")
        stocks = self.alpha_vantage.search_stock(symbol)

        log.debug("Filtering search stock results...")
        filtered_stocks = []
        for stock in stocks:
            if (
                stock.type == "Equity"
                and stock.region == "United States"
                and stock.currency == "USD"
            ):
                filtered_stocks.append(stock)
        log.debug(f"Filtered {len(stocks) - len(filtered_stocks)} stocks")

        return filtered_stocks

    def get_prices(
        self, stock: str, start_date: dt.datetime, end_date: dt.datetime
    ) -> StockPrices:
        return self.polygon.get_stock_prices(stock, start_date, end_date)

    def get_latest_price(self, stock: str) -> float:
        now = dt.datetime.now()
        return self.get_prices(stock, now - dt.timedelta(days=7), now).prices[-1].price

    def get_statistics(self, symbol: str) -> CompanyStatistics | None:
        return self.alpha_vantage.get_company_statistics(symbol)
