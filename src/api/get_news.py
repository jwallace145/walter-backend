import json

from dataclasses import dataclass
from src.api.common.exceptions import BadRequest, StockDoesNotExist
from src.api.common.methods import WalterAPIMethod, HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.stocks.client import WalterStocksAPI


@dataclass
class GetNews(WalterAPIMethod):

    API_NAME = "GetNews"
    REQUIRED_HEADERS = [
        {"Content-Type": "application/json"},
    ]
    REQUIRED_FIELDS = ["stock"]
    EXCEPTIONS = [BadRequest, StockDoesNotExist]

    walter_db: WalterDB
    walter_stocks_api: WalterStocksAPI

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
        walter_stocks_api: WalterStocksAPI,
    ) -> None:
        super().__init__(
            GetNews.API_NAME,
            GetNews.REQUIRED_HEADERS,
            GetNews.REQUIRED_FIELDS,
            GetNews.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db
        self.walter_stocks_api = walter_stocks_api

    def execute(self, event: dict, authenticated_email: str = None) -> dict:
        body = json.loads(event["body"])
        stock = body["stock"].upper()
        news = self.walter_stocks_api.get_news(stock)
        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Retrieved news!",
            data=news.to_dict(),
        )

    def validate_fields(self, event: dict) -> None:
        body = json.loads(event["body"])

        symbol = body["stock"].upper()
        stock = self.walter_stocks_api.get_stock(symbol)
        if stock is None:
            raise StockDoesNotExist("Stock does not exist!")

        if self.walter_db.get_stock(symbol) is None:
            self.walter_db.add_stock(stock)

    def is_authenticated_api(self) -> bool:
        return False
