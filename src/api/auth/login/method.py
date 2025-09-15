import datetime as dt
import json
from dataclasses import dataclass
from typing import Optional

from user_agents import parse

from src.api.auth.login.models import LoginResponse
from src.api.common.exceptions import (
    BadRequest,
    InvalidEmail,
    InvalidPassword,
    UserDoesNotExist,
)
from src.api.common.methods import HTTPStatus, Status, WalterAPIMethod
from src.api.common.models import Response
from src.api.common.utils import is_valid_email
from src.auth.authenticator import WalterAuthenticator
from src.auth.models import Tokens
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.database.sessions.models import Session
from src.database.users.models import User
from src.environment import Domain
from src.metrics.client import DatadogMetricsClient
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass(kw_only=True)
class Login(WalterAPIMethod):
    """
    WalterAPI: Login
    """

    API_NAME = "Login"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"content-type": "application/json"}
    REQUIRED_FIELDS = ["email", "password"]
    EXCEPTIONS = [
        (BadRequest, HTTPStatus.BAD_REQUEST),
        (UserDoesNotExist, HTTPStatus.NOT_FOUND),
        (InvalidPassword, HTTPStatus.UNAUTHORIZED),
        (InvalidEmail, HTTPStatus.UNAUTHORIZED),
    ]

    walter_sm: WalterSecretsManagerClient

    def __init__(
        self,
        domain: Domain,
        walter_authenticator: WalterAuthenticator,
        metrics: DatadogMetricsClient,
        walter_db: WalterDB,
        walter_sm: WalterSecretsManagerClient,
    ) -> None:
        super().__init__(
            domain,
            Login.API_NAME,
            Login.REQUIRED_QUERY_FIELDS,
            Login.REQUIRED_HEADERS,
            Login.REQUIRED_FIELDS,
            Login.EXCEPTIONS,
            walter_authenticator,
            metrics,
            walter_db,
        )
        self.walter_sm = walter_sm

    def execute(self, event: dict, session: Optional[Session]) -> Response:
        email = json.loads(event["body"])["email"].lower()
        user = self._verify_user_exists(email)
        self._verify_password(event, user)
        tokens = self._create_tokens(user)
        self._create_session(user, tokens, event)
        self._update_last_active_date(user)
        return self._create_response(
            HTTPStatus.OK,
            Status.SUCCESS,
            "User logged in successfully!",
            LoginResponse(user, tokens).to_dict(),
        )

    def validate_fields(self, event: dict) -> None:
        body = json.loads(event["body"])

        # verify email is valid
        email = body["email"].lower()
        if not is_valid_email(email):
            raise InvalidEmail("Invalid email!")

    def is_authenticated_api(self) -> bool:
        return False

    def _verify_user_exists(self, email: str) -> User:
        log.info(f"Verifying user exists with email: '{email}'")
        user = self.db.get_user_by_email(email)
        if user is None:
            raise UserDoesNotExist(f"User with email '{email}' does not exist!")
        log.info("Verified user exists!")
        return user

    def _verify_password(self, event: dict, user: User) -> None:
        log.info("Verifying password matches stored password hash")
        password = json.loads(event["body"])["password"]
        if not self.authenticator.check_secret(password, user.password_hash):
            log.error("Password incorrect!")
            raise InvalidPassword("Password incorrect!")
        log.info("Verified password matches!")

    def _create_tokens(self, user: User) -> Tokens:
        log.info(f"Generating tokens for user '{user.user_id}'")
        tokens = self.authenticator.generate_tokens(user.user_id)
        log.info(f"Created tokens with ID '{tokens.jti}'")
        return tokens

    def _update_last_active_date(self, user: User) -> None:
        log.info("Updating user last active time")
        user.last_active_date = dt.datetime.now(dt.UTC)
        self.db.update_user(user)
        log.info("Updated user last active time")

    def _create_session(self, user: User, tokens: Tokens, event: dict) -> None:
        log.info(
            f"Creating new session for user '{user.user_id}' with session ID '{tokens.jti}'"
        )
        client_ip = self._get_client_ip(event)
        client_device = self._get_client_device(event)
        self.db.create_session(user.user_id, tokens.jti, client_ip, client_device)
        log.info(
            f"Created new session for user '{user.user_id}' with token ID '{tokens.jti}'"
        )

    def _get_client_ip(self, event: dict) -> str:
        return (
            event.get("requestContext", {})
            .get("identity", {})
            .get("sourceIp", "UNKNOWN")
        )

    def _get_client_device(self, event: dict) -> str:
        user_agent_string = event.get("headers", {}).get("User-Agent", "")
        user_agent = parse(user_agent_string)
        return str(
            user_agent
        )  # cast to string to get string-friendly representation of device
