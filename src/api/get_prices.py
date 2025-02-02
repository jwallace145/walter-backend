import json
from dataclasses import dataclass
from typing import List

from src.api.common.exceptions import BadRequest, StockDoesNotExist
from src.api.common.methods import HTTPStatus, Status
from src.api.common.methods import WalterAPIMethod
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.database.stocks.models import Stock
from src.stocks.client import WalterStocksAPI
from src.stocks.polygon.models import StockPrice
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class GetPrices(WalterAPIMethod):
    """
    WalterAPI: GetPrices

    This API gets the latest time-series pricing data for the given stock.
    """

    API_NAME = "GetPrices"
    REQUIRED_HEADERS = {"content-type": "application/json"}
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
            GetPrices.API_NAME,
            GetPrices.REQUIRED_HEADERS,
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
        stock = self._verify_stock_exists(stock)
        prices = self._get_prices(stock)
        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Retrieved prices!",
            data={
                "stock": stock.symbol,
                "prices": [prices.to_dict() for prices in prices],
            },
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return False

    def _verify_stock_exists(self, symbol: str) -> Stock | None:
        log.info("Verifying stock exists...")
        cached_stock = self.walter_db.get_stock(symbol)
        if cached_stock is None:
            log.info("Stock not found in WalterDB. Checking AlphaVantage...")
            stock = self.walter_stocks_api.get_stock(symbol)
            if stock is None:
                log.error("Stock does not exist!")
                raise StockDoesNotExist("Stock does not exist!")
            log.info("Adding stock to WalterDB...")
            self.walter_db.add_stock(stock)
            return stock
        log.info(
            f"Stock found in WalterDB:\n{json.dumps(cached_stock.to_dict(), indent=4)}"
        )
        return cached_stock

    def _get_prices(self, stock: Stock) -> List[StockPrice]:
        log.info("Getting prices from Polygon")
        return self.walter_stocks_api.get_prices(stock.symbol).prices
