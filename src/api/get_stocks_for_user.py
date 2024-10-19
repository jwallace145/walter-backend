import json
from dataclasses import dataclass

from src.api.exceptions import UserDoesNotExist, InvalidEmail
from src.api.methods import WalterAPIMethod
from src.api.models import HTTPStatus, Status
from src.api.utils import is_valid_email
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class GetStocksForUser(WalterAPIMethod):

    API_NAME = "WalterAPI: GetStocksForUser"
    REQUIRED_FIELDS = ["email"]
    EXCEPTIONS = [InvalidEmail, UserDoesNotExist]

    walter_db: WalterDB
    walter_sm: WalterSecretsManagerClient

    def __init__(
        self, walter_db: WalterDB, walter_sm: WalterSecretsManagerClient
    ) -> None:
        super().__init__(
            GetStocksForUser.API_NAME,
            GetStocksForUser.REQUIRED_FIELDS,
            GetStocksForUser.EXCEPTIONS,
        )
        self.walter_db = walter_db
        self.walter_sm = walter_sm

    def execute(self, event: dict) -> dict:
        body = json.loads(event["body"])

        email = body["email"]
        user = self.walter_db.get_user(email)
        if user is None:
            raise UserDoesNotExist("User not found!")

        stocks = self.walter_db.get_stocks_for_user(user)

        return self._create_response(
            HTTPStatus.OK,
            Status.SUCCESS,
            [stock.to_dict() for stock in stocks.values()],
        )

    def validate_fields(self, event: dict) -> None:
        body = json.loads(event["body"])
        email = body["email"]

        if not is_valid_email(email):
            raise InvalidEmail("Invalid email!")

    def is_authenticated_api(self) -> bool:
        return True

    def get_jwt_secret_key(self) -> str:
        return self.walter_sm.get_jwt_secret_key()
