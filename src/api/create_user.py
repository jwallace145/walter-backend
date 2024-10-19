import json

from src.api.exceptions import (
    InvalidEmail,
    InvalidUsername,
    UserAlreadyExists,
    BadRequest,
)
from src.api.methods import WalterAPIMethod
from src.api.models import HTTPStatus, Status
from src.api.utils import is_valid_username, is_valid_email
from src.database.client import WalterDB
from src.utils.log import Logger

log = Logger(__name__).get_logger()


class CreateUser(WalterAPIMethod):

    API_NAME = "WalterAPI: CreateUser"
    REQUIRED_FIELDS = ["email", "username", "password"]
    EXCEPTIONS = [BadRequest, InvalidEmail, InvalidUsername, UserAlreadyExists]

    def __init__(
        self,
        walter_db: WalterDB,
    ) -> None:
        super().__init__(
            CreateUser.API_NAME, CreateUser.REQUIRED_FIELDS, CreateUser.EXCEPTIONS
        )
        self.walter_db = walter_db

    def execute(self, event: dict) -> dict:
        body = json.loads(event["body"])
        self.walter_db.create_user(
            email=body["email"],
            username=body["username"],
            password=body["password"],
        )
        return self._create_response(HTTPStatus.OK, Status.SUCCESS, "User created!")

    def validate_fields(self, event: dict) -> None:
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

    def is_authenticated_api(self) -> bool:
        return False

    def get_jwt_secret_key(self) -> str:
        raise ValueError(f"{self.api_name} is not an authenticated API!")
