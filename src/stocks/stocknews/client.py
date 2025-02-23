from dataclasses import dataclass
from datetime import datetime

import requests

from src.config import CONFIG
from src.database.stocks.models import Stock
from src.stocks.stocknews.exceptions import StockNewsAPINewsNotFound
from src.stocks.stocknews.models import StockNewsArticle, StockNews
from src.utils.log import Logger
from src.utils.web_scraper import WebScraper

log = Logger(__name__).get_logger()


@dataclass
class StockNewsClient:
    """
    StockNews API Client

    https://stocknewsapi.com/
    """

    BASE_URL = "https://stocknewsapi.com/api/v1"
    DATESTAMP_FORMAT = "%Y-%m-%d"
    ARTICLE_TIMESTAMP_FORMAT = "%a, %d %b %Y %H:%M:%S %z"

    api_key: str
    web_scraper: WebScraper

    def __post_init__(self) -> None:
        log.debug("Initializing StockNewsClient")

    def get_news(
        self,
        stock: Stock,
        start_date: datetime,
        end_date: datetime,
        limit: int = CONFIG.news_summary.number_of_articles,
    ) -> StockNews:
        start_datestamp = StockNewsClient._get_datestamp(start_date)
        end_datestamp = StockNewsClient._get_datestamp(end_date)
        log.info(
            f"Getting news for stock '{stock.symbol}' from '{start_datestamp}' to '{end_datestamp}' limiting to {limit} articles"
        )
        url = self._get_news_url(stock.symbol)

        response = requests.get(url).json()
        if response == {} or len(response["data"]) == 0:
            log.warning(
                f"No news found for '{stock.symbol}' from '{start_date.strftime('%Y-%m-%d')}' to '{end_date.strftime('%Y-%m-%d')}!"
            )
            raise StockNewsAPINewsNotFound(f"No news found for '{stock.symbol}'!")

        log.info(
            f"Returned {len(response['data'])} articles for '{stock.symbol.upper()}'! Parsing {limit} articles..."
        )

        # iterate over returned articles and scrape contents until the number of
        # articles parsed limit is reached or there are no more articles to parse
        articles = []
        index = 0
        while len(articles) < limit and index < len(response["data"]):
            article = response["data"][index]
            url = article["news_url"]
            contents = self.web_scraper.scrape(url)

            # ensure web scraped news from article is not empty
            if contents:
                article = StockNewsClient._get_stock_news_article(article, contents)
                articles.append(article)

            index += 1

        return StockNews(
            stock=stock.symbol,
            start_date=start_date,
            end_date=end_date,
            articles=articles,
        )

    def _get_news_url(
        self, symbol: str, limit: int = CONFIG.news_summary.number_of_articles
    ) -> str:
        return f"{StockNewsClient.BASE_URL}?tickers={symbol.upper()}&items={limit}&token={self.api_key}&date=last30days"

    @staticmethod
    def _get_stock_news_article(article: dict, contents: str) -> StockNewsArticle:
        published_timestamp = StockNewsClient._get_timestamp_from_stock_news_article(
            article["date"]
        )

        # source is not a required key in the stock news article response obj
        source = "N/A"
        if "source" in article:
            source = article["source"]

        return StockNewsArticle(
            news_url=article["news_url"],
            image_url=article["image_url"],
            title=article["title"],
            text=article["text"],
            source=source,
            contents=contents,
            published_timestamp=published_timestamp,
        )

    @staticmethod
    def _get_timestamp_from_stock_news_article(timestamp: str) -> datetime:
        return datetime.strptime(timestamp, StockNewsClient.ARTICLE_TIMESTAMP_FORMAT)

    @staticmethod
    def _get_datestamp(timestamp: datetime) -> str:
        return timestamp.strftime(StockNewsClient.DATESTAMP_FORMAT)
