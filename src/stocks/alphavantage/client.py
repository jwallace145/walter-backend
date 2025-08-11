import datetime
import datetime as dt
import json
from dataclasses import dataclass
from typing import List

import requests

from src.config import CONFIG
from src.stocks.alphavantage.models import (
    CompanyOverview,
    CompanySearch,
    NewsArticle,
    CompanyStatistics,
)
from src.utils.log import Logger
from src.utils.web_scraper import WebScraper

log = Logger(__name__).get_logger()

#############
# CONSTANTS #
#############

LOOKBACK_DATE = dt.datetime.today() - dt.timedelta(
    days=CONFIG.news_summary.lookback_window_days
)
"""(datetime): The lookback date to use for getting stock news."""

TODAY = dt.datetime.today()
"""(datetime): The current date."""

##########
# CLIENT #
##########


@dataclass
class AlphaVantageClient:
    """
    AlphaVantage Client

    docs: https://www.alphavantage.co/documentation/
    """

    BASE_URL = "https://www.alphavantage.co"
    METHOD_URL_FORMAT = "{base_url}/query?function={method}{args}{key}"

    GET_COMPANY_OVERVIEW_METHOD = "OVERVIEW"
    GET_NEWS_SENTIMENT_METHOD = "NEWS_SENTIMENT"
    GET_SYMBOL_SEARCH_METHOD = "SYMBOL_SEARCH"

    GET_NEWS_SENTIMENT_METHOD_TIMESTAMP_FORMAT = "%Y%m%dT%H%M%S"

    api_key: str
    web_scraper: WebScraper

    def __post_init__(self) -> None:
        log.debug("Initializing AlphaVantage Client")

    def get_company_statistics(self, symbol: str) -> CompanyStatistics | None:
        """
        Get the company statistics.

        Args:
            symbol: The stock symbol of the company.

        Returns:
            (CompanyStatistics): The company statistics or `None` if not found.
        """
        log.info(f"Getting company statistics for '{symbol}'")
        url = self._get_company_overview_url(symbol)
        response = requests.get(url).json()

        # if empty dict response from alpha vantage then assume stock does not exist
        if response == {}:
            return None

        statistics = CompanyStatistics(
            market_cap=response["MarketCapitalization"],
            ebitda=response["EBITDA"],
            pe_ratio=response["PERatio"],
            dividend_yield=response["DividendYield"],
            eps=response["EPS"],
            fifty_two_week_high=response["52WeekHigh"],
            fifty_two_week_low=response["52WeekLow"],
        )

        log.info(f"Returned company statistics for '{symbol}'")
        log.debug(f"CompanyStatistics:\n{json.dumps(statistics.to_dict(), indent=4)}")

        return statistics

    def get_company_overview(self, symbol: str) -> CompanyOverview | None:
        """
        Get the company overview.

        Args:
            symbol: The stock symbol of the company.

        Returns:
            The company overview or `None` if not found.
        """
        log.info(f"Getting company overview for '{symbol}'")
        url = self._get_company_overview_url(symbol)
        response = requests.get(url).json()

        # if empty dict response from alpha vantage then assume stock does not exist
        if response == {}:
            return None

        overview = CompanyOverview(
            symbol=response["Symbol"],
            name=response["Name"],
            description=response["Description"],
            exchange=response["Exchange"],
            sector=response["Sector"],
            industry=response["Industry"],
            official_site=response["OfficialSite"],
            address=response["Address"],
        )
        log.info(f"Returned company overview for '{symbol}'")
        log.debug(f"CompanyOverview:\n{json.dumps(overview.to_dict(), indent=4)}")

        return overview

    def search_stock(self, symbol: str) -> List[CompanySearch]:
        log.info(f"Searching for stocks with tickers similar to '{symbol}'")
        url = self._get_search_stock_url(symbol)
        response = requests.get(url).json()

        if response == {}:
            log.warning(f"No stocks found for symbol '{symbol}'!")
            return None

        return [
            AlphaVantageClient._get_company_search(stock)
            for stock in response["bestMatches"]
        ]

    def _get_company_overview_url(self, symbol: str) -> str:
        return self._get_method_url(
            method=AlphaVantageClient.GET_COMPANY_OVERVIEW_METHOD,
            args={"symbol": symbol},
        )

    def _get_news_url(
        self,
        symbol: str,
        start_date: dt.datetime = LOOKBACK_DATE,
        end_date: dt.datetime = TODAY,
    ) -> str:
        start_date_str = start_date.strftime("%Y%m%dT%H%M")
        end_date_str = end_date.strftime("%Y%m%dT%H%M")

        if start_date >= end_date:
            raise ValueError(
                f"Cannot create GetNews URL with start date greater than end date! Start: '{start_date_str}' End: '{end_date_str}'"
            )

        return self._get_method_url(
            method=AlphaVantageClient.GET_NEWS_SENTIMENT_METHOD,
            args={
                "tickers": symbol,
                "sort": "RELEVANCE",
                "time_from": start_date_str,
                "time_to": end_date_str,
            },
        )

    def _get_search_stock_url(self, symbol: str) -> str:
        return self._get_method_url(
            method=AlphaVantageClient.GET_SYMBOL_SEARCH_METHOD,
            args={"keywords": symbol},
        )

    def _get_method_url(self, method: str, args: dict) -> str:
        args_str = ""
        for name, value in args.items():
            args_str += f"&{name}={value}"
        return AlphaVantageClient.METHOD_URL_FORMAT.format(
            base_url=AlphaVantageClient.BASE_URL,
            method=method,
            args=args_str,
            key=f"&apikey={self.api_key}",
        )

    @staticmethod
    def _get_company_search(stock: dict) -> CompanySearch:
        return CompanySearch(
            symbol=stock["1. symbol"],
            name=stock["2. name"],
            type=stock["3. type"],
            region=stock["4. region"],
            currency=stock["8. currency"],
            match_score=stock["9. matchScore"],
        )

    @staticmethod
    def _get_news_article(article: dict, contents: str) -> NewsArticle:
        published_timestamp = datetime.datetime.strptime(
            article["time_published"],
            AlphaVantageClient.GET_NEWS_SENTIMENT_METHOD_TIMESTAMP_FORMAT,
        )
        return NewsArticle(
            title=article["title"],
            url=article["url"],
            published_timestamp=published_timestamp,
            authors=article["authors"],
            source=article["source"],
            summary=article["summary"],
            contents=contents,
        )
