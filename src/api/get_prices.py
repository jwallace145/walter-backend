from dataclasses import dataclass
from typing import List

from src.api.common.exceptions import BadRequest, StockDoesNotExist
from src.api.common.methods import HTTPStatus, Status
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import Response
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.database.stocks.models import Stock
from src.stocks.client import WalterStocksAPI
from src.stocks.polygon.models import StockPrice
from src.utils.log import Logger
import datetime as dt

log = Logger(__name__).get_logger()


@dataclass
class GetPrices(WalterAPIMethod):
    """
    WalterAPI: GetPrices

    This API gets stock pricing data from Polygon
    for a given period of time.
    """

    API_NAME = "GetPrices"
    REQUIRED_QUERY_FIELDS = ["stock", "start_date", "end_date"]
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
            GetPrices.API_NAME,
            GetPrices.REQUIRED_QUERY_FIELDS,
            GetPrices.REQUIRED_HEADERS,
            GetPrices.REQUIRED_FIELDS,
            GetPrices.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db
        self.walter_stocks_api = walter_stocks_api

    def execute(self, event: dict, authenticated_email: str) -> Response:
        stock = WalterAPIMethod.get_query_field(event, "stock")
        start_date = self._get_date_from_url(event, "start_date")
        end_date = self._get_date_from_url(event, "end_date")
        self._validate_dates(start_date, end_date)
        stock = self._verify_stock_exists(stock)
        prices = self._get_prices(stock, start_date, end_date)
        return Response(
            api_name=GetPrices.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Retrieved prices!",
            data={
                "stock": stock.symbol,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "num_prices": len(prices),
                "prices": [prices.to_dict() for prices in prices],
            },
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return False

    def _get_date_from_url(self, event: dict, date: str) -> dt.datetime:
        date_str = ""
        try:
            date_str = WalterAPIMethod.get_query_field(event, date)
            return dt.datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            log.warning(f"Unable to parse date: {date_str}!")
            raise BadRequest(f"Unable to parse date: {date_str}!")

    def _validate_dates(self, start_date: dt.datetime, end_date: dt.datetime) -> None:
        if start_date > end_date:
            log.warning("Start date must be before end date!")
            raise BadRequest("Start date must be before end date!")

    def _verify_stock_exists(self, symbol: str) -> Stock | None:
        log.info("Verifying stock exists...")
        cached_stock = self.walter_db.get_stock(symbol)
        if cached_stock is None:
            log.info("Stock not found in WalterDB. Checking WalterStocksAPI...")
            stock = self.walter_stocks_api.get_stock(symbol)
            if stock is None:
                log.error("Stock does not exist!")
                raise StockDoesNotExist("Stock does not exist!")
            log.info("Adding stock to WalterDB...")
            self.walter_db.add_stock(stock)
            return stock
        log.info("Stock found in WalterDB!")
        return cached_stock

    def _get_prices(
        self, stock: Stock, start_date: dt.datetime, end_date: dt.datetime
    ) -> List[StockPrice]:
        log.info("Getting prices from WalterStocksAPI...")
        return self.walter_stocks_api.get_prices(
            stock.symbol, start_date, end_date
        ).prices
