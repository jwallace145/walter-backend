import json
from dataclasses import dataclass

from src.api.common.exceptions import (
    BadRequest,
    NotAuthenticated,
    UserDoesNotExist,
    StockDoesNotExist,
    MaximumNumberOfStocks,
)
from src.api.common.methods import WalterAPIMethod, Status, HTTPStatus
from src.api.common.models import Response
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.config import CONFIG
from src.database.client import WalterDB
from src.database.stocks.models import Stock
from src.database.users.models import User
from src.database.userstocks.models import UserStock
from src.stocks.client import WalterStocksAPI
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class AddStock(WalterAPIMethod):
    """
    WalterAPI: AddStock

    This API adds a stock to the user's portfolio in WalterDB.
    """

    API_NAME = "AddStock"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer", "content-type": "application/json"}
    REQUIRED_FIELDS = ["stock", "quantity"]
    EXCEPTIONS = [
        BadRequest,
        NotAuthenticated,
        UserDoesNotExist,
        StockDoesNotExist,
        MaximumNumberOfStocks,
    ]

    walter_db: WalterDB
    walter_stocks_api: WalterStocksAPI
    walter_sm: WalterSecretsManagerClient

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
        walter_stocks_api: WalterStocksAPI,
        walter_sm: WalterSecretsManagerClient,
    ) -> None:
        super().__init__(
            AddStock.API_NAME,
            AddStock.REQUIRED_QUERY_FIELDS,
            AddStock.REQUIRED_HEADERS,
            AddStock.REQUIRED_FIELDS,
            AddStock.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db
        self.walter_stocks_api = walter_stocks_api
        self.walter_sm = walter_sm

    def execute(self, event: dict, authenticated_email: str) -> Response:
        body = json.loads(event["body"])
        symbol = body["stock"].upper()
        quantity = body["quantity"]
        stock = self._verify_stock_exists(symbol)
        user = self._verify_user_exists(authenticated_email)
        self._verify_max_num_stocks(authenticated_email)
        user_stock = self._add_stock_to_user_portfolio(user.user_id, stock, quantity)
        return Response(
            api_name=AddStock.API_NAME,
            http_status=HTTPStatus.CREATED,
            status=Status.SUCCESS,
            message="Stock added!",
            data={
                "user": user.email,
                "stock": user_stock.stock_symbol.upper(),
                "quantity": user_stock.quantity,
            },
        )

    def validate_fields(self, event: dict) -> None:
        body = json.loads(event["body"])
        quantity = body["quantity"]
        self._verify_quantity_field(quantity)

    def is_authenticated_api(self) -> bool:
        return True

    def _verify_quantity_field(self, quantity: str) -> bool:
        if quantity is None or not isinstance(quantity, (int, float)):
            raise BadRequest("Quantity must be a number!")
        if quantity <= 0:
            raise BadRequest("Quantity must be a positive number!")

    def _verify_stock_exists(self, symbol: str) -> Stock:
        log.info(f"Verifying stock exists with symbol '{symbol}'")
        stock = self.walter_db.get_stock(symbol)
        if stock is None:
            log.warning(
                "Stock does not exist in WalterDB! Getting stock from WalterStocksAPI..."
            )
            stock = self.walter_stocks_api.get_stock(symbol)
            if stock is None:
                raise StockDoesNotExist("Stock does not exist!")
            log.info("Stock exists in WalterStocksAPI! Adding stock to WalterDB...")
            self.walter_db.add_stock(stock)
        log.info("Verified stock exists!")
        return stock

    def _verify_user_exists(self, email: str) -> User:
        log.info(f"Verifying user exists with email '{email}'")
        user = self.walter_db.get_user_by_email(email)
        if user is None:
            raise UserDoesNotExist("User does not exist!")
        log.info("Verified user exists!")
        return user

    def _verify_max_num_stocks(self, email: str) -> None:
        log.info("Verifying max number of stocks in user's portfolio...")
        user = self.walter_db.get_user(email)  # TODO: this is a pointless network call
        stocks = self.walter_db.get_stocks_for_user(user)

        if len(stocks) >= CONFIG.user_portfolio.maximum_number_of_stocks:
            raise MaximumNumberOfStocks("Max number of stocks!")

    def _add_stock_to_user_portfolio(
        self, user_id: str, stock: Stock, quantity: float
    ) -> UserStock:
        log.info(
            f"Adding {quantity} shares of stock '{stock.symbol.upper()}' to user's portfolio..."
        )
        user_stock = UserStock(
            user_id=user_id,
            stock_symbol=stock.symbol,
            quantity=quantity,
        )
        self.walter_db.add_stock_to_user_portfolio(user_stock)
        return user_stock
