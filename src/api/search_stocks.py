from dataclasses import dataclass

from src.api.common.exceptions import BadRequest
from src.api.common.methods import WalterAPIMethod, HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.stocks.client import WalterStocksAPI
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class SearchStocks(WalterAPIMethod):
    """
    WalterAPI: SearchStock
    """

    API_NAME = "SearchStock"
    REQUIRED_QUERY_FIELDS = ["symbol"]
    REQUIRED_HEADERS = {}
    REQUIRED_FIELDS = []
    EXCEPTIONS = [BadRequest]

    walter_stocks_api: WalterStocksAPI

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_stocks_api: WalterStocksAPI,
    ) -> None:
        super().__init__(
            SearchStocks.API_NAME,
            SearchStocks.REQUIRED_QUERY_FIELDS,
            SearchStocks.REQUIRED_HEADERS,
            SearchStocks.REQUIRED_FIELDS,
            SearchStocks.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_stocks_api = walter_stocks_api

    def execute(self, event: dict, authenticated_email: str = None) -> dict:
        stock = self._get_symbol(event)
        stocks = self.walter_stocks_api.search_stock(stock)
        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Retrieved matching stocks!",
            data={"stocks": [stock.to_dict() for stock in stocks]},
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return False

    def _get_symbol(self, event: dict) -> str | None:
        return event["queryStringParameters"]["symbol"]
