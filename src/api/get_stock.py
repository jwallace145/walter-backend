from src.api.exceptions import BadRequest, StockDoesNotExist
from src.api.methods import WalterAPIMethod, HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.stocks.client import WalterStocksAPI


class GetStock(WalterAPIMethod):

    API_NAME = "GetStock"
    REQUIRED_QUERY_FIELDS = ["symbol"]
    REQUIRED_FIELDS = []
    EXCEPTIONS = [BadRequest, StockDoesNotExist]

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
        walter_stocks_api: WalterStocksAPI,
    ) -> None:
        super().__init__(
            GetStock.API_NAME,
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

        # early return if stock is in db
        stock = self.walter_db.get_stock(symbol)
        if stock is not None:
            return self._create_response(
                http_status=HTTPStatus.OK,
                status=Status.SUCCESS,
                message="Retrieved stock details!",
                data={
                    "stock": stock.to_dict(),
                },
            )

        # if stock is not found in stocks api, raise error
        stock = self.walter_stocks_api.get_stock(symbol)
        if stock is None:
            raise StockDoesNotExist("Stock does not exist!")

        # add stock that wasn't in db to db with info from stocks api and return
        self.walter_db.add_stock(stock)
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
