import json
from dataclasses import dataclass

from src.api.exceptions import UserDoesNotExist, InvalidEmail
from src.api.models import HTTPStatus, Status, create_response
from src.api.utils import is_valid_email, authenticate_request
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class GetStocksForUser:

    API_NAME = "WalterAPI: GetStocksForUser"
    REQUIRED_FIELDS = ["email"]
    EXCEPTIONS = [InvalidEmail, UserDoesNotExist]

    walter_db: WalterDB
    walter_sm: WalterSecretsManagerClient

    def invoke(self, event: dict) -> dict:
        log.info(f"Getting stocks for user with event: {json.dumps(event, indent=4)}")

        if not self._is_valid_request(event):
            error_msg = "Client bad request to get stocks for user!"
            log.error(error_msg)
            return create_response(
                GetStocksForUser.API_NAME,
                HTTPStatus.BAD_REQUEST,
                Status.FAILURE,
                error_msg,
            )

        return self._get_stocks_for_user(event)

    def _is_valid_request(self, event: dict) -> bool:
        body = json.loads(event["body"])
        for field in GetStocksForUser.REQUIRED_FIELDS:
            if field not in body:
                return False
        return True

    def _get_stocks_for_user(self, event: dict) -> dict:
        try:
            body = json.loads(event["body"])
            email = body["email"]

            if not is_valid_email(email):
                raise InvalidEmail("Invalid email!")

            user = self.walter_db.get_user(email)
            if user is None:
                raise UserDoesNotExist("User not found!")

            authenticate_request(event, self.walter_sm.get_jwt_secret_key())

            stocks = self.walter_db.get_stocks_for_user(user)

            return create_response(
                GetStocksForUser.API_NAME,
                HTTPStatus.OK,
                Status.SUCCESS,
                [stock.to_dict() for stock in stocks.values()],
            )
        except Exception as exception:
            status = HTTPStatus.INTERNAL_SERVER_ERROR
            for e in GetStocksForUser.EXCEPTIONS:
                if isinstance(exception, e):
                    status = HTTPStatus.OK
                    break
            return create_response(
                GetStocksForUser.API_NAME,
                status,
                Status.FAILURE,
                str(exception),
            )
