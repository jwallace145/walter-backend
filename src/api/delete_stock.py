import json

from dataclasses import dataclass
from src.api.common.exceptions import (
    BadRequest,
    NotAuthenticated,
    StockDoesNotExist,
    UserDoesNotExist,
)
from src.api.common.methods import WalterAPIMethod, Status, HTTPStatus
from src.api.common.models import Response
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.database.users.models import User
from src.database.userstocks.models import UserStock
from src.stocks.client import WalterStocksAPI

from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class DeleteStock(WalterAPIMethod):

    API_NAME = "DeleteStock"
    REQUIRED_QUERY_FIELDS = []
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
            DeleteStock.REQUIRED_QUERY_FIELDS,
            DeleteStock.REQUIRED_HEADERS,
            DeleteStock.REQUIRED_FIELDS,
            DeleteStock.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db
        self.walter_stocks_api = walter_stocks_api
        self.walter_sm = walter_sm

    def execute(self, event: dict, authenticated_email: str) -> Response:
        user = self._verify_user_exists(authenticated_email)
        body = json.loads(event["body"])
        self.walter_db.delete_stock_from_user_portfolio(
            UserStock(
                user_id=user.user_id,
                stock_symbol=body["stock"],
                quantity=0,
            )
        )
        return Response(
            api_name=DeleteStock.API_NAME,
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

    def _verify_user_exists(self, email: str) -> User:
        log.info(f"Verifying user exists with email '{email}'")
        user = self.walter_db.get_user_by_email(email)
        if user is None:
            raise UserDoesNotExist("User does not exist!")
        log.info("Verified user exists!")
        return user
