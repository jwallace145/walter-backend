import json

from src.api.common.exceptions import (
    InvalidEmail,
    BadRequest,
    NotAuthenticated,
    UserDoesNotExist,
    StockDoesNotExist,
)
from src.api.common.methods import WalterAPIMethod, Status, HTTPStatus
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.database.userstocks.models import UserStock
from src.stocks.client import WalterStocksAPI
from src.utils.log import Logger

log = Logger(__name__).get_logger()


class AddStock(WalterAPIMethod):

    API_NAME = "AddStock"
    REQUIRED_FIELDS = ["stock", "quantity"]
    EXCEPTIONS = [
        BadRequest,
        NotAuthenticated,
        InvalidEmail,
        UserDoesNotExist,
        StockDoesNotExist,
    ]

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
            AddStock.REQUIRED_FIELDS,
            AddStock.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db
        self.walter_stocks_api = walter_stocks_api
        self.walter_sm = walter_sm

    def execute(self, event: dict, authenticated_email: str) -> dict:
        body = json.loads(event["body"])
        stock = body["stock"].upper()
        quantity = body["quantity"]
        self.walter_db.add_stock_to_user_portfolio(
            UserStock(
                user_email=authenticated_email,
                stock_symbol=stock,
                quantity=quantity,
            )
        )
        return self._create_response(
            http_status=HTTPStatus.CREATED,
            status=Status.SUCCESS,
            message="Stock added!",
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
        return True
