import datetime as dt
from dataclasses import dataclass

from src.ai.client import WalterAI
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.config import CONFIG
from src.database.stocks.models import Stock
from src.stocks.alphavantage.exceptions import CompanyNewsNotFound
from src.stocks.alphavantage.models import CompanyNews
from src.stocks.client import WalterStocksAPI
from src.summaries.exceptions import GenerateNewsSummaryFailure
from src.summaries.models import NewsSummary
from src.utils.log import Logger

log = Logger(__name__).get_logger()

###########
# METRICS #
###########

METRICS_CREATE_NEWS_SUMMARY_INPUT_TOKEN_SIZE = "CreateNewsSummaryInputTokenSize"
"""(str): This metric emits the number of tokens input to WalterAI to generate the news summary."""

METRICS_CREATE_NEWS_SUMMARY_OUTPUT_TOKEN_SIZE = "CreateNewsSummaryOutputTokenSize"
"""(str): This metric emits the number of tokens output from WalterAI to generate the news summary."""

METRICS_NUMBER_OF_ARTICLES_PARSED = "CreateNewsSummaryNumberOfArticlesParsed"
"""(str): The total number of articles parsed by Walter to create a news summary."""

METRICS_CREATE_NEWS_SUMMARY_SUCCESS = "CreateNewsSummarySuccess"
"""(str): This metric emits when Walter successfully generates a news summary for the given stock."""

METRICS_CREATE_NEWS_SUMMARY_FAILURE = "CreateNewsSummaryFailure"
"""(str): This metric emits when Walter cannot a news summary for the given stock."""

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
    walter_cw: WalterCloudWatchClient

    def __post_init__(self) -> None:
        log.debug("Initializing WalterNewsSummaryClient")

    def generate(
        self,
        stock: Stock,
        start_date: dt.datetime,
        end_date: dt.datetime,
        number_of_articles: int = CONFIG.news_summary.number_of_articles,
        context: str = CONFIG.news_summary.context,
        prompt: str = CONFIG.news_summary.prompt,
        max_length: int = CONFIG.news_summary.max_length,
    ) -> NewsSummary:
        log.info(
            f"Generating '{stock.symbol}' news summary for date '{end_date.strftime('%Y-%m-%d')}'"
        )
        try:
            news = self._get_stock_news(stock, start_date, end_date, number_of_articles)
            formatted_prompt = self._get_formatted_prompt(news, context, prompt)
            summary = self._generate_news_summary(news, formatted_prompt, max_length)
            self._emit_success_metrics(news, formatted_prompt, summary)
            return summary
        except CompanyNewsNotFound:
            self._emit_failure_metrics()
            raise GenerateNewsSummaryFailure(
                f"Cannot generate news summary for stock '{stock.upper()}'! No stock news found."
            )

    def _get_stock_news(
        self,
        stock: Stock,
        start_date: dt.datetime,
        end_date: dt.datetime,
        numbers_of_articles: int = CONFIG.news_summary.number_of_articles,
    ) -> CompanyNews:
        news = self.walter_stock_api.get_news(
            stock, start_date, end_date, numbers_of_articles
        )
        log.info(
            f"Successfully returned {len(news.articles)} '{stock.symbol}' news articles!"
        )
        return news

    def _get_formatted_prompt(
        self,
        news: CompanyNews,
        context: str = CONFIG.news_summary.context,
        prompt: str = CONFIG.news_summary.prompt,
    ) -> str:
        formatted_prompt = f"Context: {context}\nPrompt: {prompt.format(stock=news.stock, news=news.to_dict())}"
        return formatted_prompt

    def _generate_news_summary(
        self,
        news: CompanyNews,
        formatted_prompt: str,
        max_length: int = CONFIG.news_summary.max_length,
    ) -> NewsSummary:
        log.info(f"Generating news summary for '{news.stock.upper()}' stock news...")
        summary = self.walter_ai.generate_response(
            prompt=formatted_prompt, max_output_tokens=max_length
        )
        log.info(f"Successfully generated '{news.stock.upper()}' stock news summary!")
        return NewsSummary(
            stock=news.stock,
            company=news.company,
            datestamp=news.end_date,
            model_name=self.walter_ai.get_model().get_name(),
            news=news,
            summary=summary,
        )

    def _emit_success_metrics(
        self, news: CompanyNews, formatted_prompt: str, summary: NewsSummary
    ) -> None:
        log.info("Emitting CreateNewsSummary success metrics...")
        input_token_size = len(formatted_prompt.split())
        self.walter_cw.emit_metric(
            METRICS_CREATE_NEWS_SUMMARY_INPUT_TOKEN_SIZE, input_token_size
        )
        output_token_size = len(summary.get_summary()["summary"].split())
        self.walter_cw.emit_metric(
            METRICS_CREATE_NEWS_SUMMARY_OUTPUT_TOKEN_SIZE, output_token_size
        )
        num_articles = len(news.articles)
        self.walter_cw.emit_metric(METRICS_NUMBER_OF_ARTICLES_PARSED, num_articles)
        self.walter_cw.emit_metric(METRICS_CREATE_NEWS_SUMMARY_SUCCESS, True)
        self.walter_cw.emit_metric(METRICS_CREATE_NEWS_SUMMARY_FAILURE, False)

    def _emit_failure_metrics(self) -> None:
        log.info("Emitting CreateNewsSummary failure metrics!")
        self.walter_cw.emit_metric(METRICS_CREATE_NEWS_SUMMARY_SUCCESS, False)
        self.walter_cw.emit_metric(METRICS_CREATE_NEWS_SUMMARY_FAILURE, True)
