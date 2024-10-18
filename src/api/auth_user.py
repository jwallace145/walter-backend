import json
from dataclasses import dataclass

from src.api.exceptions import UserDoesNotExist, InvalidPassword, InvalidEmail
from src.api.models import HTTPStatus, Status, create_response
from src.api.utils import is_valid_email
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.utils.auth import check_password, generate_token
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class AuthUser:

    API_NAME = "WalterAPI: AuthUser"
    REQUIRED_FIELDS = ["email", "password"]
    EXCEPTIONS = [UserDoesNotExist, InvalidPassword, InvalidEmail]

    walter_db: WalterDB
    walter_sm: WalterSecretsManagerClient

    jwt_token_key: str = None  # lazy init

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
            if not is_valid_email(email):
                raise InvalidEmail("Invalid email!")

            user = self.walter_db.get_user(email)
            if user is None:
                raise UserDoesNotExist("User not found!")

            password = body["password"]
            if not check_password(password, user.password_hash):
                raise InvalidPassword("Password incorrect!")

            token = generate_token(email, self._get_jwt_token_key())

            return create_response(
                AuthUser.API_NAME, HTTPStatus.OK, Status.SUCCESS, token
            )
        except Exception as exception:
            status = HTTPStatus.INTERNAL_SERVER_ERROR
            for e in AuthUser.EXCEPTIONS:
                if isinstance(exception, e):
                    status = HTTPStatus.OK
                    break
            return create_response(
                AuthUser.API_NAME,
                status,
                Status.FAILURE,
                str(exception),
            )

    def _get_jwt_token_key(self) -> str:
        if self.jwt_token_key is None:
            self.jwt_token_key = self.walter_sm.get_jwt_secret_key()
        return self.jwt_token_key
