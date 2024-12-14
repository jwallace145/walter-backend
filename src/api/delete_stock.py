import json

from dataclasses import dataclass
from src.api.common.exceptions import BadRequest, NotAuthenticated, StockDoesNotExist
from src.api.common.methods import WalterAPIMethod, Status, HTTPStatus
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.database.userstocks.models import UserStock
from src.stocks.client import WalterStocksAPI


@dataclass
class DeleteStock(WalterAPIMethod):

    API_NAME = "DeleteStock"
    REQUIRED_HEADERS = {"Authorization": "Bearer", "content-type": "application/json"}
    REQUIRED_FIELDS = ["stock"]
    EXCEPTIONS = [
        BadRequest,
        NotAuthenticated,
        StockDoesNotExist,
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
            DeleteStock.API_NAME,
            DeleteStock.REQUIRED_HEADERS,
            DeleteStock.REQUIRED_FIELDS,
            DeleteStock.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db
        self.walter_stocks_api = walter_stocks_api
        self.walter_sm = walter_sm

    def execute(self, event: dict, authenticated_email: str) -> dict:
        body = json.loads(event["body"])
        self.walter_db.delete_stock_from_user_portfolio(
            UserStock(
                user_email=authenticated_email,
                stock_symbol=body["stock"],
                quantity=0,
            )
        )
        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Stock deleted!",
        )

    def validate_fields(self, event: dict) -> None:
        body = json.loads(event["body"])

        stock_symbol = body["stock"]
        stock = self.walter_stocks_api.get_stock(stock_symbol)
        if stock is None:
            raise StockDoesNotExist("Stock does not exist!")

    def is_authenticated_api(self) -> bool:
        return True
