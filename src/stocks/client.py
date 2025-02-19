from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

from src.config import CONFIG
from src.database.stocks.models import Stock
from src.database.userstocks.models import UserStock
from src.stocks.alphavantage.client import AlphaVantageClient
from src.stocks.alphavantage.models import CompanyOverview, CompanySearch, CompanyNews
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
        return Portfolio(stocks, user_stocks, prices)

    def get_stock(self, symbol: str) -> Stock | None:
        log.info(f"Getting stock '{symbol}'")
        overview = self.alpha_vantage.get_company_overview(symbol)
        return (
            WalterStocksAPI._get_stock_from_company_overview(overview)
            if overview
            else None
        )

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

    def get_prices(self, stock: str) -> StockPrices:
        return self.polygon.get_stock_prices(stock)

    def get_news(
        self,
        stock: Stock,
        start_date: datetime,
        end_date: datetime,
        number_of_articles: int = CONFIG.news_summary.number_of_articles,
    ) -> CompanyNews:
        log.info(f"Getting news for stock '{stock.symbol}'")
        return self.alpha_vantage.get_news(
            stock, start_date, end_date, number_of_articles
        )

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
