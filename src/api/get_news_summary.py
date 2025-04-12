from dataclasses import dataclass

from src.api.common.exceptions import BadRequest, StockDoesNotExist
from src.api.common.methods import WalterAPIMethod, HTTPStatus, Status
from src.api.common.models import Response
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.database.stocks.models import Stock
from src.news.bucket import NewsSummariesBucket
from src.news.queue import NewsSummariesQueue, NewsSummaryRequest
from src.stocks.client import WalterStocksAPI
from src.summaries.models import NewsSummary
from src.utils.log import Logger

log = Logger(__name__).get_logger()

NUMBER_OF_ARTICLES_TO_RETURN_LIMIT = 3
"""(int): This config truncates the remaining news articles from the GetNewsSummary response after reaching the limit."""


@dataclass
class GetNewsSummary(WalterAPIMethod):
    """
    WalterAPI: GetNewsSummary
    """

    API_NAME = "GetNewsSummary"
    REQUIRED_QUERY_FIELDS = ["symbol"]
    REQUIRED_HEADERS = {}
    REQUIRED_FIELDS = []
    EXCEPTIONS = [BadRequest, StockDoesNotExist]

    walter_db: WalterDB
    walter_stocks_api: WalterStocksAPI
    news_summaries_bucket: NewsSummariesBucket
    news_summaries_queue: NewsSummariesQueue

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
        walter_stocks_api: WalterStocksAPI,
        news_summaries_bucket: NewsSummariesBucket,
        news_summaries_queue: NewsSummariesQueue,
    ) -> None:
        super().__init__(
            GetNewsSummary.API_NAME,
            GetNewsSummary.REQUIRED_QUERY_FIELDS,
            GetNewsSummary.REQUIRED_HEADERS,
            GetNewsSummary.REQUIRED_FIELDS,
            GetNewsSummary.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db
        self.walter_stocks_api = walter_stocks_api
        self.news_summaries_bucket = news_summaries_bucket
        self.news_summaries_queue = news_summaries_queue

    def execute(self, event: dict, authenticated_email: str = None) -> Response:
        symbol = self._get_symbol(event)

        stock = self._verify_stock_exists(symbol)
        if stock is None:
            raise StockDoesNotExist("Stock does not exist!")

        summary = self._check_archive_for_summary(stock)
        if summary is not None:
            return Response(
                api_name=GetNewsSummary.API_NAME,
                http_status=HTTPStatus.OK,
                status=Status.SUCCESS,
                message="Retrieved news!",
                data={
                    "summary": summary.summary,
                    "articles": [
                        article.get_metadata() for article in summary.news.articles
                    ][:NUMBER_OF_ARTICLES_TO_RETURN_LIMIT],
                },
            )

        self._add_news_summary_request(stock.symbol)
        return Response(
            api_name=GetNewsSummary.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="News summary not found! Generating news summary now...",
            data={"summary": "Generating news summary, check back later..."},
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return False

    def _get_symbol(self, event: dict) -> str | None:
        return event["queryStringParameters"]["symbol"]

    def _verify_stock_exists(self, symbol: str) -> Stock | None:
        log.info("Validating stock...")
        stock = self.walter_db.get_stock(symbol)
        if stock is None:
            log.info("Stock not found in WalterDB! Getting stock from StocksAPI...")
            stock = self.walter_stocks_api.get_stock(symbol)
            if stock is None:
                log.info("Stock does not exist!")
                raise StockDoesNotExist("Stock does not exist!")
            log.info("Stock returned from StocksAPI! Adding stock to WalterDB...")
            self.walter_db.add_stock(stock)
        return stock

    def _check_archive_for_summary(self, stock: Stock) -> NewsSummary | None:
        log.info("Checking archive for news summary...")
        summary = self.news_summaries_bucket.get_news_summary(stock)
        if summary is not None:
            log.info("Found news summary in archive!")
            return summary
        log.info("News summary not found in archive!")

    def _add_news_summary_request(self, stock: str) -> None:
        log.info(f"Adding news summary request for stock '{stock}' to queue...")
        request = NewsSummaryRequest(stock=stock)
        self.news_summaries_queue.add_news_summary_request(request)
