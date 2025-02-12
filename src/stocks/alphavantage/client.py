import datetime as dt
import json
import re
from dataclasses import dataclass
from typing import List

import requests

from src.stocks.alphavantage.models import (
    CompanyOverview,
    CompanyNews,
    CompanySearch,
    NewsArticle,
)
from src.utils.log import Logger
from src.utils.web_scraper import WebScraper

log = Logger(__name__).get_logger()

#############
# CONSTANTS #
#############

ONE_YEAR_AGO = dt.datetime.today() - dt.timedelta(days=365)
"""(datetime): Exactly one year ago from the current date."""

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

    api_key: str
    web_scraper: WebScraper

    def __post_init__(self) -> None:
        log.debug("Initializing AlphaVantage Client")

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

    def get_news(self, symbol: str, date: dt, limit: int) -> CompanyNews | None:
        """
        Get relevant company news.

        This method is used by various APIs and therefore needs to be quick to
        ensure API requests do not time out/take too long. The limit method arg
        allows callers to limit how many articles this method returns. Default
        value of 3 ensures fast response times.

        Args:
            symbol: The stock symbol of the company.
            date: The most recent news date to fetch.
            limit: The number of news articles to return.

        Returns:
            The latest company news or `None` if not found.
        """
        log.info(
            f"Getting company news for '{symbol}' with most recent news date '{date}'"
        )
        url = self._get_news_url(symbol, date)
        response = requests.get(url).json()

        if response == {}:
            log.info("No news found for '{symbol}'")
            return None

        log.info(f"Parsing {limit} articles for '{symbol}'")

        articles = []
        for article in response["feed"][:limit]:
            title = self._format_title(article["title"])
            url = article["url"]
            text = self.web_scraper.scrape(url)
            articles.append(NewsArticle(title=title, url=url, contents=text))

        return CompanyNews(stock=symbol, articles=articles)

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
        return self._get_method_url(method="OVERVIEW", args={"symbol": symbol})

    def _get_news_url(
        self,
        symbol: str,
        time_from: dt.datetime = ONE_YEAR_AGO,
        time_to: dt.datetime = TODAY,
    ) -> str:
        return self._get_method_url(
            method="NEWS_SENTIMENT",
            args={
                "tickers": symbol,
                "sort": "RELEVANCE",
                "time_from": time_from.strftime("%Y%m%dT%H%M"),
                "time_to": time_to.strftime("%Y%m%dT%H%M"),
            },
        )

    def _get_search_stock_url(self, symbol: str) -> str:
        return self._get_method_url(method="SYMBOL_SEARCH", args={"keywords": symbol})

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
    def _get_company_search(stock: dict) -> str:
        return CompanySearch(
            symbol=stock["1. symbol"],
            name=stock["2. name"],
            type=stock["3. type"],
            region=stock["4. region"],
            currency=stock["8. currency"],
            match_score=stock["9. matchScore"],
        )

    @staticmethod
    def _format_title(title: str) -> str:
        cleaned_title = re.sub(r"[^a-zA-Z0-9\s]", "", title)
        cleaned_title = cleaned_title.lower()
        formatted_title = cleaned_title.replace(" ", "-")
        truncated_title = formatted_title[:64]
        return truncated_title
