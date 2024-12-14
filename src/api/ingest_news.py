from dataclasses import dataclass

from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.database.stocks.models import Stock
from src.knowledge.base import WalterKnowledgeBase
from src.stocks.alphavantage.models import CompanyNews
from src.stocks.client import WalterStocksAPI
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class IngestNews(WalterAPIMethod):
    """
    WalterAPI - IngestNews

    Scan WalterDB for all stocks and pull relevant market news and add
    to knowledge base.
    """

    # TODO: Add authorization so that only admins can call this API with an admin token

    API_NAME = "IngestNews"
    REQUIRED_HEADERS = {}
    REQUIRED_FIELDS = []
    EXCEPTIONS = []

    walter_db: WalterDB
    walter_stocks_api: WalterStocksAPI
    walter_knowledge_base: WalterKnowledgeBase

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
        walter_stocks_api: WalterStocksAPI,
        walter_knowledge_base: WalterKnowledgeBase,
    ) -> None:
        super().__init__(
            IngestNews.API_NAME,
            IngestNews.REQUIRED_HEADERS,
            IngestNews.REQUIRED_FIELDS,
            IngestNews.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db
        self.walter_stocks_api = walter_stocks_api
        self.walter_knowledge_base = walter_knowledge_base

    def execute(self, event: dict, authenticated_email: str) -> dict:
        stocks = self._get_stocks_from_db()
        for stock in stocks:
            news = self._get_stock_news(stock)
            self._dump_news(news)
        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Ingested news!",
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return False

    def _get_stocks_from_db(self) -> list:
        log.info("Getting all stocks from WalterDB")
        stocks = self.walter_db.get_all_stocks()
        log.info(f"Successfully retrieved {len(stocks)} stocks from WalterDB!")
        return stocks

    def _get_stock_news(self, stock: Stock) -> CompanyNews:
        log.info("Getting stocks news")
        news = self.walter_stocks_api.get_news(stock.symbol)
        log.info("Successfully retrieved stocks news!")
        return news

    def _dump_news(self, news: CompanyNews) -> None:
        log.info("Dumping news to S3")
        self.walter_knowledge_base.add_news(news)
        log.info("Successfully dumped news to S3!")
