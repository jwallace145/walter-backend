import json
from dataclasses import dataclass

from src.api.exceptions import (
    InvalidEmail,
    InvalidUsername,
    UserAlreadyExists,
    NotAuthenticated,
)
from src.api.models import HTTPStatus, Status, create_response
from src.api.utils import is_valid_username, is_valid_email
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class CreateUser:

    API_NAME = "WalterAPI: CreateUser"
    REQUIRED_FIELDS = ["email", "username", "password"]
    EXCEPTIONS = [NotAuthenticated, InvalidEmail, InvalidUsername, UserAlreadyExists]

    walter_db: WalterDB
    walter_sm: WalterSecretsManagerClient

    def invoke(self, event: dict) -> dict:
        log.info(f"Creating user with event: {json.dumps(event, indent=4)}")

        if not self._is_valid_request(event):
            error_msg = "Client bad request to create user!"
            log.error(error_msg)
            return create_response(
                CreateUser.API_NAME, HTTPStatus.BAD_REQUEST, Status.FAILURE, error_msg
            )

        return self._create_user(event)

    def _is_valid_request(self, event: dict) -> bool:
        body = json.loads(event["body"])
        for field in CreateUser.REQUIRED_FIELDS:
            if field not in body:
                return False
        return True

    def _create_user(self, event: dict) -> dict:
        try:
            body = json.loads(event["body"])
            email = body["email"]

            if not is_valid_email(email):
                raise InvalidEmail("Invalid email!")

            username = body["username"]
            if not is_valid_username(username):
                raise InvalidUsername("Invalid username!")

            user = self.walter_db.get_user(email)
            if user is not None:
                raise UserAlreadyExists("User already exists!")

            self.walter_db.create_user(
                email=email,
                username=username,
                password=body["password"],
            )

            return create_response(
                CreateUser.API_NAME, HTTPStatus.OK, Status.SUCCESS, "User created!"
            )
        except Exception as exception:
            for e in CreateUser.EXCEPTIONS:
                if isinstance(exception, e):
                    return create_response(
                        CreateUser.API_NAME,
                        HTTPStatus.OK,
                        Status.FAILURE,
                        str(exception),
                    )
            return create_response(
                CreateUser.API_NAME,
                HTTPStatus.INTERNAL_SERVER_ERROR,
                Status.FAILURE,
                str(exception),
            )
