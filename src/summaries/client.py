import datetime as dt
from dataclasses import dataclass

from src.ai.client import WalterAI
from src.config import CONFIG
from src.stocks.alphavantage.exceptions import CompanyNewsNotFound
from src.stocks.alphavantage.models import CompanyNews
from src.stocks.client import WalterStocksAPI
from src.summaries.exceptions import GenerateNewsSummaryFailure
from src.summaries.models import NewsSummary
from src.utils.log import Logger

log = Logger(__name__).get_logger()

#############
# CONSTANTS #
#############

CONTEXT = "You are a AI investment portfolio advisor that summarizes stock market news and gives readers digestible, business insights about the latest stock market movements to help them stay informed."
"""(str): The context used to give to the LLM to generate news summaries."""

PROMPT = "Summarize the following news article about the stock '{stock}' to give a well-written concise update of the stock and any market news relating to it but write it with headers and bodies so it looks like a formatted report. Include data where possible and only focus on the most important updates, do not simply summarize each article separately:\n{news}"
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
        start_date: dt.datetime,
        end_date: dt.datetime,
        number_of_articles: int = CONFIG.news_summary.number_of_articles,
    ) -> NewsSummary:
        log.info(
            f"Generating '{stock.upper()}' news summary for date '{end_date.strftime('%Y-%m-%d')}'"
        )
        try:
            news = self._get_stock_news(stock, start_date, end_date, number_of_articles)
            return self._generate_news_summary(news)
        except CompanyNewsNotFound:
            raise GenerateNewsSummaryFailure(
                f"Cannot generate news summary for stock '{stock.upper()}'! No stock news found."
            )

    def _get_stock_news(
        self,
        stock: str,
        start_date: dt.datetime,
        end_date: dt.datetime,
        numbers_of_articles: int = CONFIG.news_summary.number_of_articles,
    ) -> CompanyNews:
        news = self.walter_stock_api.get_news(
            stock, start_date, end_date, numbers_of_articles
        )
        log.info(
            f"Successfully returned {len(news.articles)} '{stock.upper()}' news articles!"
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
            datestamp=news.end_date,
            model_name=self.walter_ai.get_model().get_name(),
            news=news,
            summary=summary,
        )
