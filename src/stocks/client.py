from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

from src.database.stocks.models import Stock
from src.database.userstocks.models import UserStock
from src.stocks.alphavantage.client import AlphaVantageClient
from src.stocks.alphavantage.models import CompanyOverview, CompanyNews, CompanySearch
from src.stocks.models import Portfolio
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
        log.info(f"Getting stock '{symbol}'")
        overview = self.alpha_vantage.get_company_overview(symbol)
        return (
            WalterStocksAPI._get_stock_from_company_overview(overview)
            if overview
            else None
        )

    def get_news(self, symbol: str) -> CompanyNews | None:
        log.info(f"Getting news '{symbol}'")
        return self.alpha_vantage.get_news(symbol)

    def search_stock(self, symbol: str) -> List[CompanySearch]:
        log.info(f"Searching for stocks similar to '{symbol}'")
        return self.alpha_vantage.search_stock(symbol)

    def get_prices(self, stock: str) -> StockPrices:
        return self.polygon.get_stock_prices(stock)

    @staticmethod
    def _get_stock_from_company_overview(overview: CompanyOverview) -> Stock:
        return Stock(
            symbol=overview.symbol,
            company=overview.name,
            exchange=overview.exchange,
            sector=overview.sector,
            industry=overview.industry,
            description=overview.description,
            official_site=overview.official_site,
            address=overview.address,
        )
