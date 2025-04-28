import datetime as dt
from dataclasses import dataclass
from typing import Optional

from src.api.common.exceptions import UserDoesNotExist, InvalidEmail, NotAuthenticated
from src.api.common.methods import HTTPStatus, Status
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import Response
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.database.users.models import User
from src.stocks.client import WalterStocksAPI
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class GetPortfolio(WalterAPIMethod):

    API_NAME = "GetPortfolio"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer"}
    REQUIRED_FIELDS = []
    EXCEPTIONS = [NotAuthenticated, InvalidEmail, UserDoesNotExist]

    walter_db: WalterDB
    walter_sm: WalterSecretsManagerClient
    walter_stocks_api: WalterStocksAPI

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
        walter_sm: WalterSecretsManagerClient,
        walter_stocks_api: WalterStocksAPI,
    ) -> None:
        super().__init__(
            GetPortfolio.API_NAME,
            GetPortfolio.REQUIRED_QUERY_FIELDS,
            GetPortfolio.REQUIRED_HEADERS,
            GetPortfolio.REQUIRED_FIELDS,
            GetPortfolio.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db
        self.walter_sm = walter_sm
        self.walter_stocks_api = walter_stocks_api

    def execute(self, event: dict, authenticated_email: str) -> Response:
        user = self._verify_user_exists(authenticated_email)

        user_stocks = self.walter_db.get_stocks_for_user(user)
        stocks = self.walter_db.get_stocks(list(user_stocks.keys()))

        end = dt.datetime.now(dt.UTC)
        start = end - dt.timedelta(days=7)
        portfolio = self.walter_stocks_api.get_portfolio(
            user_stocks, stocks, start, end
        )

        return Response(
            api_name=GetPortfolio.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Retrieved portfolio!",
            data={
                "total_equity": portfolio.get_total_equity(),
                "stocks": [stock.to_dict() for stock in portfolio.get_stock_equities()],
            },
        )

    def validate_fields(self, event: dict) -> None:
        return

    def is_authenticated_api(self) -> bool:
        return True

    def _verify_user_exists(self, email: str) -> Optional[User]:
        log.info(f"Verifying user exists with email '{email}'")
        user = self.walter_db.get_user(email)
        if user is None:
            raise UserDoesNotExist(f"User not found with email '{email}'!")
        log.info("Verified user exists!")
        return user
