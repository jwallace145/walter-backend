import json
from dataclasses import dataclass

from src.api.exceptions import UserDoesNotExist, InvalidEmail, NotAuthenticated
from src.api.models import HTTPStatus, Status, create_response
from src.api.utils import is_valid_email, authenticate_request
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.database.userstocks.models import UserStock
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class AddStock:

    API_NAME = "WalterAPI: AddStock"
    REQUIRED_FIELDS = ["email", "stock", "quantity"]
    EXCEPTIONS = [NotAuthenticated, UserDoesNotExist, InvalidEmail, NotAuthenticated]

    walter_db: WalterDB
    walter_sm: WalterSecretsManagerClient

    def invoke(self, event: dict) -> dict:
        log.info(
            f"Adding stock to user portfolio with event: {json.dumps(event, indent=4)}"
        )

        if not self._is_valid_request(event):
            error_msg = "Client bad request to add stock!"
            log.error(error_msg)
            return create_response(
                AddStock.API_NAME, HTTPStatus.BAD_REQUEST, Status.FAILURE, error_msg
            )

        return self._add_stock(event)

    def _is_valid_request(self, event: dict) -> bool:
        body = json.loads(event["body"])
        for field in AddStock.REQUIRED_FIELDS:
            if field not in body:
                return False
        return True

    def _add_stock(self, event: dict) -> dict:
        try:
            body = json.loads(event["body"])
            email = body["email"]

            if not is_valid_email(email):
                raise InvalidEmail("Invalid email!")

            user = self.walter_db.get_user(email)
            if user is None:
                raise UserDoesNotExist("User not found!")

            authenticate_request(event, self.walter_sm.get_jwt_secret_key())

            stock = UserStock(
                user_email=email,
                stock_symbol=body["stock"],
                quantity=body["quantity"],
            )

            self.walter_db.add_stock_to_user_portfolio(stock)

            return create_response(
                AddStock.API_NAME, HTTPStatus.OK, Status.SUCCESS, "Stock added!"
            )
        except Exception as exception:
            status = HTTPStatus.INTERNAL_SERVER_ERROR
            for e in AddStock.EXCEPTIONS:
                if isinstance(exception, e):
                    status = HTTPStatus.OK
                    break
            return create_response(
                AddStock.API_NAME,
                status,
                Status.FAILURE,
                str(exception),
            )
