import json
from dataclasses import dataclass

from src.api.models import HTTPStatus, Status, Response
from src.clients import walter_db
from src.database.userstocks.models import UserStock
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class AddStock:

    API_NAME = "WalterAPI: AddStock"
    REQUIRED_FIELDS = ["email", "stock", "quantity"]

    event: dict

    def invoke(self) -> dict:
        log.info(
            f"Adding stock to user portfolio with event: {json.dumps(self.event, indent=4)}"
        )

        if not self._is_valid_request():
            error_msg = "Client bad request to add stock!"
            log.error(error_msg)
            return self._create_response(
                HTTPStatus.BAD_REQUEST, Status.FAILURE, error_msg
            )

        return self._add_stock()

    def _is_valid_request(self) -> bool:
        body = json.loads(self.event["body"])
        for field in AddStock.REQUIRED_FIELDS:
            if field not in body:
                return False
        return True

    def _add_stock(self) -> dict:
        try:
            body = json.loads(self.event["body"])
            stock = UserStock(
                user_email=body["email"],
                stock_symbol=body["stock"],
                quantity=body["quantity"],
            )
            walter_db.add_stock_to_user_portfolio(stock)
            return self._generate_response(
                HTTPStatus.OK, Status.SUCCESS, "Stock added!"
            )
        except Exception as exception:
            return self._generate_response(
                HTTPStatus.INTERNAL_SERVER_ERROR, Status.FAILURE, str(exception)
            )

    def _generate_response(
        self, http_status: HTTPStatus, status: Status, message: str
    ) -> dict:
        return Response(
            api_name=AddStock.API_NAME,
            http_status=http_status,
            status=status,
            message=message,
        ).to_json()
