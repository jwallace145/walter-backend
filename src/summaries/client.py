import datetime as dt
from dataclasses import dataclass

from src.ai.client import WalterAI
from src.config import CONFIG
from src.stocks.alphavantage.models import CompanyNews
from src.stocks.client import WalterStocksAPI
from src.summaries.models import NewsSummary
from src.utils.log import Logger

log = Logger(__name__).get_logger()

#############
# CONSTANTS #
#############

CONTEXT = "You are a financial AI advisor that summaries market news and gives readers digestible, business casual insights about the latest market movements."
"""(str): The context used to give to the LLM to generate news summaries."""

PROMPT = "Summarize the following news article about the stock '{stock}' to give a well-written concise update of the stock and any market news relating to it but write it with headers and bodies so it looks like a formatted report:\n{news}"
"""(str): The prompt used to give to the LLM to generate news summaries."""

SUMMARY_MAX_LENGTH = CONFIG.news_summary.max_length
"""(int): The length of the news summary is controlled by the max generation length of the LLM response."""

##########
# CLIENT #
##########


@dataclass
class WalterNewsSummaryClient:
    """
    WalterNewsSummaryClient
    """

    walter_stock_api: WalterStocksAPI
    walter_ai: WalterAI

    def __post_init__(self) -> None:
        log.debug("Initializing WalterNewsSummaryClient")

    def generate(
        self,
        stock: str,
        datestamp: dt.datetime,
        number_of_articles=CONFIG.news_summary.number_of_articles,
    ) -> NewsSummary | None:
        log.info(
            f"Generating '{stock.upper()}' stock news summary for date: '{datestamp.strftime('%Y-%m-%d')}'"
        )
        news = self._get_stock_news(stock, datestamp, number_of_articles)
        return self._generate_news_summary(news)

    def _get_stock_news(
        self,
        stock: str,
        datestamp: dt.datetime,
        numbers_of_articles: int = CONFIG.news_summary.number_of_articles,
    ) -> CompanyNews:
        log.info(
            f"Getting latest '{stock.upper()}' stock news with latest published date: '{datestamp.strftime('%Y-%m-%d')}'"
        )
        news = self.walter_stock_api.get_news(stock, datestamp, numbers_of_articles)
        if not news:
            raise ValueError(
                f"No '{stock.upper()}' stock news articles returned with latest published date: '{datestamp.strftime('%Y-%m-%d')}'!"
            )
        log.info(
            f"Successfully returned {len(news.articles)} '{stock.upper()}' stock news articles!"
        )
        return news

    def _generate_news_summary(self, news: CompanyNews) -> NewsSummary:
        log.info(f"Generating news summary for '{news.stock.upper()}' stock news...")
        summary = self.walter_ai.generate_response(
            context=CONTEXT,
            prompt=PROMPT.format(stock=news.stock, news=news.to_dict()),
            max_output_tokens=SUMMARY_MAX_LENGTH,
        )
        log.info(f"Successfully generated '{news.stock.upper()}' stock news summary!")
        return NewsSummary(
            stock=news.stock,
            datestamp=news.datestamp,
            model_name=self.walter_ai.get_model().get_name(),
            articles=news.articles,
            summary=summary,
        )
