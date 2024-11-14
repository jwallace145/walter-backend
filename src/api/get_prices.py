import json

from src.api.exceptions import BadRequest, StockDoesNotExist
from src.api.methods import HTTPStatus, Status
from src.api.methods import WalterAPIMethod
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.stocks.client import WalterStocksAPI


class GetPrices(WalterAPIMethod):

    API_NAME = "GetPrices"
    REQUIRED_FIELDS = ["stock"]
    EXCEPTIONS = [BadRequest, StockDoesNotExist]

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
        walter_stocks_api: WalterStocksAPI,
    ) -> None:
        super().__init__(
            GetPrices.API_NAME,
            GetPrices.REQUIRED_FIELDS,
            GetPrices.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db
        self.walter_stocks_api = walter_stocks_api

    def execute(self, event: dict, authenticated_email: str) -> dict:
        body = json.loads(event["body"])
        stock = body["stock"]
        prices = self.walter_stocks_api.get_prices(stock).prices
        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Retrieved prices!",
            data={"stock": stock, "prices": [prices.to_dict() for prices in prices]},
        )

    def validate_fields(self, event: dict) -> None:
        body = json.loads(event["body"])

        symbol = body["stock"]
        stock = self.walter_stocks_api.get_stock(symbol)
        if stock is None:
            raise StockDoesNotExist("Stock does not exist!")

        if self.walter_db.get_stock(symbol) is None:
            self.walter_db.add_stock(stock)

    def is_authenticated_api(self) -> bool:
        return False
