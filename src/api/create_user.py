import json
from dataclasses import dataclass

from src.api.models import HTTPStatus, Status, Response
from src.clients import walter_db
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class CreateUser:

    API_NAME = "WalterAPI: CreateUser"
    REQUIRED_FIELDS = ["email", "username", "password"]

    event: dict

    def invoke(self) -> dict:
        log.info(f"Creating user with event: {json.dumps(self.event, indent=4)}")

        if not self._is_valid_request():
            error_msg = "Client bad request to create user!"
            log.error(error_msg)
            return self._create_response(
                HTTPStatus.BAD_REQUEST, Status.FAILURE, error_msg
            )

        return self._create_user()

    def _is_valid_request(self) -> bool:
        body = json.loads(self.event["body"])
        for field in CreateUser.REQUIRED_FIELDS:
            if field not in body:
                return False
        return True

    def _create_user(self) -> dict:
        try:
            body = json.loads(self.event["body"])
            walter_db.create_user(
                email=body["email"],
                username=body["username"],
                password=body["password"],
            )
            return self._create_response(HTTPStatus.OK, Status.SUCCESS, "User created!")
        except Exception as exception:
            return self._create_response(
                HTTPStatus.INTERNAL_SERVER_ERROR, Status.FAILURE, str(exception)
            )

    def _create_response(
        self, http_status: HTTPStatus, status: Status, message: str
    ) -> dict:
        return Response(
            api_name=CreateUser.API_NAME,
            http_status=http_status,
            status=status,
            message=message,
        ).to_json()
