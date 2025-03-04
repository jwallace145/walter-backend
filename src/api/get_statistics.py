from dataclasses import dataclass

from src.api.common.exceptions import BadRequest, NotAuthenticated, StockDoesNotExist
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.stocks.client import WalterStocksAPI
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class GetStatistics(WalterAPIMethod):
    """
    WalterAPI: GetStatistics
    """

    SYMBOL_QUERY_FIELD = "symbol"

    API_NAME = "GetStatistics"
    REQUIRED_QUERY_FIELDS = [SYMBOL_QUERY_FIELD]
    REQUIRED_HEADERS = {}
    REQUIRED_FIELDS = []
    EXCEPTIONS = [BadRequest, NotAuthenticated, StockDoesNotExist]

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_stocks_api: WalterStocksAPI,
    ) -> None:
        super().__init__(
            GetStatistics.API_NAME,
            GetStatistics.REQUIRED_QUERY_FIELDS,
            GetStatistics.REQUIRED_HEADERS,
            GetStatistics.REQUIRED_FIELDS,
            GetStatistics.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_stocks_api = walter_stocks_api

    def execute(self, event: dict, authenticated_email: str) -> dict:
        symbol = WalterAPIMethod.get_query_field(
            event, GetStatistics.SYMBOL_QUERY_FIELD
        )
        statistics = self.walter_stocks_api.get_statistics(symbol)
        if not statistics:
            raise StockDoesNotExist("Stock does not exist!")
        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Retrieved company statistics!",
            data={"statistics": statistics.to_dict()},
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return False
