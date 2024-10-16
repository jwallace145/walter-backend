import json
from dataclasses import dataclass

from src.api.models import HTTPStatus, Status, create_response
from src.database.client import WalterDB
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class CreateUser:

    API_NAME = "WalterAPI: CreateUser"
    REQUIRED_FIELDS = ["email", "username", "password"]

    walter_db: WalterDB

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
            self.walter_db.create_user(
                email=body["email"],
                username=body["username"],
                password=body["password"],
            )
            return create_response(
                CreateUser.API_NAME, HTTPStatus.OK, Status.SUCCESS, "User created!"
            )
        except Exception as exception:
            return create_response(
                CreateUser.API_NAME,
                HTTPStatus.INTERNAL_SERVER_ERROR,
                Status.FAILURE,
                str(exception),
            )
