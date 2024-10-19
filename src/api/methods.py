import json
from abc import ABC, abstractmethod
from typing import List, Union

from src.api.exceptions import BadRequest, NotAuthenticated
from src.api.models import HTTPStatus, Response, Status
from src.api.utils import get_token
from src.utils.auth import decode_token
from src.utils.log import Logger

log = Logger(__name__).get_logger()


class WalterAPIMethod(ABC):
    def __init__(
        self, api_name: str, required_fields: List[str], exceptions: List[Exception]
    ) -> None:
        self.api_name = api_name
        self.required_fields = required_fields
        self.exceptions = exceptions

    def invoke(self, event: dict) -> dict:
        log.info(f"Invoking {self.api_name} with event:\n{json.dumps(event, indent=4)}")

        try:
            self._validate_request(event)

            if self.is_authenticated_api():
                self._authenticate_request(event)

            return self.execute(event)
        except Exception as exception:
            return self._handle_exception(exception)

    def _validate_request(self, event: dict) -> None:
        self._validate_required_fields(event)
        self.validate_fields(event)

    def _validate_required_fields(self, event: dict) -> None:
        body = json.loads(event["body"])
        for field in self.required_fields:
            if field not in body:
                raise BadRequest(
                    f"Client bad request! Missing required field: '{field}'"
                )

    def _authenticate_request(self, event: dict) -> None:
        log.info("Authenticating request")
        token = get_token(event)
        if token is None:
            raise NotAuthenticated("Not authenticated!")

        decoded_token = decode_token(token, self.get_jwt_secret_key())
        if decoded_token is None:
            raise NotAuthenticated("Not authenticated!")

        body = json.loads(event["body"])
        email = body["email"]

        authenticated_user = decoded_token["sub"]
        if email != authenticated_user:
            raise NotAuthenticated("Not authenticated!")

    def _handle_exception(self, exception: Exception) -> dict:
        status = HTTPStatus.INTERNAL_SERVER_ERROR
        for e in self.exceptions:
            if isinstance(exception, e):
                status = HTTPStatus.OK
                break
        return self._create_response(
            status,
            Status.FAILURE,
            str(exception),
        )

    def _create_response(
        self,
        http_status: HTTPStatus,
        status: Status,
        message: Union[str, dict, list],
    ) -> dict:
        return Response(
            api_name=self.api_name,
            http_status=http_status,
            status=status,
            message=message,
        ).to_json()

    @abstractmethod
    def execute(self, event: dict) -> dict:
        pass

    @abstractmethod
    def validate_fields(self, event: dict) -> None:
        pass

    @abstractmethod
    def is_authenticated_api(self) -> bool:
        pass

    @abstractmethod
    def get_jwt_secret_key(self) -> str:
        pass
