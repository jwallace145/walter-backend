import json

from src.api.exceptions import (
    InvalidEmail,
    BadRequest,
    NotAuthenticated,
    UserDoesNotExist,
)
from src.api.methods import WalterAPIMethod
from src.api.models import HTTPStatus, Status
from src.api.utils import is_valid_email
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.database.userstocks.models import UserStock
from src.utils.log import Logger

log = Logger(__name__).get_logger()


class AddStock(WalterAPIMethod):

    API_NAME = "WalterAPI: AddStock"
    REQUIRED_FIELDS = ["email", "stock", "quantity"]
    EXCEPTIONS = [BadRequest, NotAuthenticated, InvalidEmail, UserDoesNotExist]

    def __init__(
        self, walter_db: WalterDB, walter_sm: WalterSecretsManagerClient
    ) -> None:
        super().__init__(
            AddStock.API_NAME, AddStock.REQUIRED_FIELDS, AddStock.EXCEPTIONS
        )
        self.walter_db = walter_db
        self.walter_sm = walter_sm

    def execute(self, event: dict) -> dict:
        body = json.loads(event["body"])
        self.walter_db.add_stock_to_user_portfolio(
            UserStock(
                user_email=body["email"],
                stock_symbol=body["stock"],
                quantity=body["quantity"],
            )
        )
        return self._create_response(HTTPStatus.OK, Status.SUCCESS, "Stock added!")

    def validate_fields(self, event: dict) -> None:
        body = json.loads(event["body"])
        email = body["email"]

        if not is_valid_email(email):
            raise InvalidEmail("Invalid email!")

        user = self.walter_db.get_user(email)
        if user is None:
            raise UserDoesNotExist("User not found!")

    def is_authenticated_api(self) -> bool:
        return True

    def get_jwt_secret_key(self) -> str:
        return self.walter_sm.get_jwt_secret_key()
