import json
from dataclasses import dataclass

from src.ai.client import WalterAI
from src.api.common.exceptions import BadRequest, StockDoesNotExist
from src.api.common.methods import WalterAPIMethod, HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.news.bucket import NewsSummariesBucket
from src.stocks.alphavantage.models import CompanyNews
from src.stocks.client import WalterStocksAPI
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class GetNewsSummary(WalterAPIMethod):
    """
    WalterAPI: GetNewsSummary
    """

    API_NAME = "GetNewsSummary"
    REQUIRED_HEADERS = {"content-type": "application/json"}
    REQUIRED_FIELDS = ["stock"]
    EXCEPTIONS = [BadRequest, StockDoesNotExist]

    walter_db: WalterDB
    walter_stocks_api: WalterStocksAPI
    walter_ai: WalterAI
    news_summaries_bucket: NewsSummariesBucket

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
        walter_stocks_api: WalterStocksAPI,
        walter_ai: WalterAI,
        news_summaries_bucket: NewsSummariesBucket,
    ) -> None:
        super().__init__(
            GetNewsSummary.API_NAME,
            GetNewsSummary.REQUIRED_HEADERS,
            GetNewsSummary.REQUIRED_FIELDS,
            GetNewsSummary.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db
        self.walter_stocks_api = walter_stocks_api
        self.walter_ai = walter_ai
        self.news_summaries_bucket = news_summaries_bucket

    def execute(self, event: dict, authenticated_email: str = None) -> dict:
        body = json.loads(event["body"])
        stock = body["stock"].upper()

        summary = self._check_s3_for_summary(stock)
        if summary is not None:
            return self._create_response(
                http_status=HTTPStatus.OK,
                status=Status.SUCCESS,
                message="Retrieved news!",
                data={"summary": summary},
            )

        news = self._get_news(stock)
        summary = self._generate_summary(news)
        self.news_summaries_bucket.put_news_summary(stock, summary)

        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Retrieved news!",
            data={"news_summary": summary},
        )

    def validate_fields(self, event: dict) -> None:
        body = json.loads(event["body"])

        log.info("Validating stock...")
        symbol = body["stock"].upper()
        if self.walter_db.get_stock(symbol) is None:
            log.info("Stock not found in WalterDB! Getting stock from StocksAPI...")
            stock = self.walter_stocks_api.get_stock(symbol)
            if stock is None:
                log.info("Stock does not exist!")
                raise StockDoesNotExist("Stock does not exist!")
            log.info("Stock returned from StocksAPI! Adding stock to WalterDB...")
            self.walter_db.add_stock(stock)

    def is_authenticated_api(self) -> bool:
        return False

    def _check_s3_for_summary(self, stock: str) -> dict | None:
        log.info("Checking S3 for news summary...")
        summary = self.news_summaries_bucket.get_news_summary(stock)
        if summary is not None:
            log.info("Found news summary in S3!")
            return summary
        log.info("News summary not found in S3!")

    def _get_news(self, stock: str) -> CompanyNews | None:
        log.info("Getting recent market news from AlphaVantage...")
        return self.walter_stocks_api.get_news(stock)

    def _generate_summary(self, news: CompanyNews, max_gen_len: int = 1000) -> str:
        log.info("Generating summary from news...")
        return self.walter_ai.generate_response(
            context="You are a financial AI advisor that summaries market news and gives readers digestible, business casual insights about the latest market movements.",
            prompt=f"Summarize the following news article about the stock '{news.symbol}':\n{news.news}",
            max_gen_len=max_gen_len,
        )
