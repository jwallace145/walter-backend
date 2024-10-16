import json
from dataclasses import dataclass

from src.api.models import HTTPStatus, Status, create_response
from src.clients import JWT_TOKEN_KEY
from src.database.client import WalterDB
from src.utils.auth import check_password, generate_token
from src.utils.log import Logger

log = Logger(__name__).get_logger()


class UserDoesNotExist(Exception):
    def __init__(self, message):
        super().__init__(message)


class InvalidPassword(Exception):
    def __init__(self, message):
        super().__init__(message)


@dataclass
class AuthUser:

    API_NAME = "WalterAPI: AuthUser"
    REQUIRED_FIELDS = ["email", "password"]

    walter_db: WalterDB

    def invoke(self, event: dict) -> dict:
        log.info(f"Authenticating user with event: {json.dumps(event, indent=4)}")

        if not self._is_valid_request(event):
            error_msg = "Client bad request to authenticate user!"
            log.error(error_msg)
            return create_response(
                AuthUser.API_NAME, HTTPStatus.BAD_REQUEST, Status.FAILURE, error_msg
            )

        return self._auth_user(event)

    def _is_valid_request(self, event: dict) -> bool:
        body = json.loads(event["body"])
        for field in AuthUser.REQUIRED_FIELDS:
            if field not in body:
                return False
        return True

    def _auth_user(self, event: dict) -> dict:
        try:
            body = json.loads(event["body"])
            email = body["email"]
            password = body["password"]

            user = self.walter_db.get_user(email)

            if user is None:
                raise UserDoesNotExist("User not found!")

            if not check_password(password, user.password_hash):
                raise InvalidPassword("Password incorrect!")

            token = generate_token(email, JWT_TOKEN_KEY)
            log.info(f"Authenticated user successfully! Generated token: {token}")

            return create_response(
                AuthUser.API_NAME, HTTPStatus.OK, Status.SUCCESS, "Authenticated user!"
            )
        except UserDoesNotExist as exception:
            return create_response(
                AuthUser.API_NAME, HTTPStatus.OK, Status.FAILURE, str(exception)
            )
        except InvalidPassword as exception:
            return create_response(
                AuthUser.API_NAME, HTTPStatus.OK, Status.FAILURE, str(exception)
            )
        except Exception as exception:
            return create_response(
                AuthUser.API_NAME,
                HTTPStatus.INTERNAL_SERVER_ERROR,
                Status.FAILURE,
                str(exception),
            )
