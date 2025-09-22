import json
from dataclasses import dataclass
from typing import Optional

from src.api.common.exceptions import (
    BadRequest,
    InvalidEmail,
    InvalidName,
    InvalidPassword,
    UserAlreadyExists,
)
from src.api.common.methods import HTTPStatus, Status, WalterAPIMethod
from src.api.common.response import Response
from src.api.common.utils import is_valid_email, is_valid_name, is_valid_password
from src.auth.authenticator import WalterAuthenticator
from src.database.client import WalterDB
from src.database.sessions.models import Session
from src.database.users.models import User
from src.environment import Domain
from src.metrics.client import DatadogMetricsClient
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class CreateUser(WalterAPIMethod):
    """
    WalterAPI - CreateUser
    """

    API_NAME = "CreateUser"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"content-type": "application/json"}
    REQUIRED_FIELDS = ["email", "first_name", "last_name", "password"]
    EXCEPTIONS = [
        (BadRequest, HTTPStatus.BAD_REQUEST),
        (InvalidEmail, HTTPStatus.BAD_REQUEST),
        (InvalidName, HTTPStatus.BAD_REQUEST),
        (InvalidPassword, HTTPStatus.BAD_REQUEST),
        (UserAlreadyExists, HTTPStatus.CONFLICT),
    ]

    def __init__(
        self,
        domain: Domain,
        walter_authenticator: WalterAuthenticator,
        metrics: DatadogMetricsClient,
        walter_db: WalterDB,
    ) -> None:
        super().__init__(
            domain,
            CreateUser.API_NAME,
            CreateUser.REQUIRED_QUERY_FIELDS,
            CreateUser.REQUIRED_HEADERS,
            CreateUser.REQUIRED_FIELDS,
            CreateUser.EXCEPTIONS,
            walter_authenticator,
            metrics,
            walter_db,
        )

    def execute(self, event: dict, session: Optional[Session]) -> Response:
        user = self._create_new_user(event)
        return self._create_response(
            http_status=HTTPStatus.CREATED,
            status=Status.SUCCESS,
            message="User created!",
            data={
                "user_id": user.user_id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "verified": user.verified,
                "sign_up_date": user.sign_up_date.isoformat(),
            },
        )

    def validate_fields(self, event: dict) -> None:
        body = json.loads(event["body"])
        email = body[
            "email"
        ].lower()  # lowercase email for case-insensitive matching for login
        first_name = body["first_name"]
        last_name = body["last_name"]
        password = body["password"]
        self._verify_email(email)
        self._verify_name(first_name, last_name)
        self._verify_password(password)
        self._verify_user(email)

    def is_authenticated_api(self) -> bool:
        return False

    def _verify_email(self, email: str) -> None:
        log.info(f"Validating email: '{email}'")
        if not is_valid_email(email):
            raise InvalidEmail("Invalid email!")
        log.info("Successfully validated email!")

    def _verify_name(self, first_name: str, last_name: str) -> None:
        log.info(f"Validating name: '{first_name} {last_name}'")
        if not is_valid_name(first_name, last_name):
            raise InvalidName(f"Invalid name '{first_name} {last_name}'!")
        log.info("Successfully validated name!")

    def _verify_password(self, password: str) -> None:
        log.info("Validating password...")
        if not is_valid_password(password):
            raise InvalidPassword(
                "Password is invalid! Must be at least 8 characters long and include 3/4 of the following: uppercase letters, lowercase letters, numbers, and special characters."
            )
        log.info("Successfully validated password!")

    def _verify_user(self, email: str) -> None:
        log.info(f"Validate user does not already exist with email: '{email}'")
        user = self.db.get_user_by_email(email)
        if user is not None:
            raise UserAlreadyExists("User already exists!")
        log.info("Successfully validated that user does not already exist!")

    def _create_new_user(self, event: dict) -> User:
        log.info("Creating new user")
        body = json.loads(event["body"])
        email = body[
            "email"
        ].lower()  # store the user email as lower-case for case-insensitive matching
        first_name = body["first_name"]
        last_name = body["last_name"]
        password = body["password"]
        return self.db.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
        )
