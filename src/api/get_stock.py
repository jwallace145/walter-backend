from dataclasses import dataclass

from src.api.common.exceptions import BadRequest, StockDoesNotExist
from src.api.common.methods import WalterAPIMethod, HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.database.stocks.models import Stock
from src.stocks.client import WalterStocksAPI

from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class GetStock(WalterAPIMethod):
    """
    WalterAPI - GetStock

    Get stock details.
    """

    API_NAME = "GetStock"
    REQUIRED_QUERY_FIELDS = ["symbol"]
    REQUIRED_HEADERS = {}
    REQUIRED_FIELDS = []
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
            GetStock.API_NAME,
            GetStock.REQUIRED_QUERY_FIELDS,
            GetStock.REQUIRED_HEADERS,
            GetStock.REQUIRED_FIELDS,
            GetStock.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db
        self.walter_stocks_api = walter_stocks_api

    def execute(self, event: dict, authenticated_email: str = None) -> dict:
        # get symbol from query params
        symbol = self._get_symbol(event)

        # check walter db for stock
        stock = self._query_walter_db(symbol)
        if stock is not None:
            return self._create_response(
                http_status=HTTPStatus.OK,
                status=Status.SUCCESS,
                message="Retrieved stock details!",
                data={
                    "stock": stock.to_dict(),
                },
            )

        stock = self._verify_stock_exists(symbol)
        self._add_stock_to_db(stock)

        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Retrieved stock details!",
            data={
                "stock": stock.to_dict(),
            },
        )

    def validate_fields(self, event: dict) -> None:
        query_parameters = event.get("queryStringParameters", {})
        for field in GetStock.REQUIRED_QUERY_FIELDS:
            if field not in query_parameters:
                raise BadRequest(
                    f"Client bad request! Missing required query parameter: '{field}'"
                )

    def is_authenticated_api(self) -> bool:
        return False

    def _get_symbol(self, event: dict) -> str | None:
        return event["queryStringParameters"]["symbol"]

    def _query_walter_db(self, symbol: str) -> Stock | None:
        log.info(f"Querying WalterDB for stock: '{symbol}'")
        stock = self.walter_db.get_stock(symbol)

        # log if the stock is not found in db for ops
        if stock is None:
            log.info("Stock not found in WalterDB!")

        return stock

    def _verify_stock_exists(self, symbol: str) -> Stock:
        log.info("Verifying stock exists")
        stock = self.walter_stocks_api.get_stock(symbol)
        if stock is None:
            log.error("Stock does not exist!")
            raise StockDoesNotExist("Stock does not exist!")
        return stock

    def _add_stock_to_db(self, stock: Stock) -> None:
        log.info(f"Adding stock '{stock.symbol}' to WalterDB")
        self.walter_db.add_stock(stock)
