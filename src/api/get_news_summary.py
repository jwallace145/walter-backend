import json
from dataclasses import dataclass

from src.api.common.exceptions import BadRequest, StockDoesNotExist
from src.api.common.methods import WalterAPIMethod, HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.news.bucket import NewsSummariesBucket
from src.news.queue import NewsSummariesQueue, NewsSummaryRequest
from src.stocks.client import WalterStocksAPI
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class GetNewsSummary(WalterAPIMethod):
    """
    WalterAPI: GetNewsSummary
    """

    API_NAME = "GetNewsSummary"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"content-type": "application/json"}
    REQUIRED_FIELDS = ["stock"]
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

        self._add_news_summary_request(stock)

        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="News summary not found, generating summary now...!",
            data={"summary": "Generating news summary, check back later..."},
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

    def _add_news_summary_request(self, stock: str) -> None:
        log.info(f"Adding news summary request for stock '{stock}' to queue...")
        request = NewsSummaryRequest(stock=stock)
        self.news_summaries_queue.add_news_summary_request(request)
