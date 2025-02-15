import json
from dataclasses import dataclass

from src.api.common.exceptions import (
    InvalidEmail,
    InvalidUsername,
    UserAlreadyExists,
    BadRequest,
)
from src.api.common.methods import HTTPStatus, Status
from src.api.common.methods import WalterAPIMethod
from src.api.common.utils import is_valid_email, is_valid_username
from src.api.send_verify_email import SendVerifyEmail
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.ses.client import WalterSESClient
from src.database.client import WalterDB
from src.templates.bucket import TemplatesBucket
from src.templates.engine import TemplatesEngine
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
    REQUIRED_FIELDS = ["email", "username", "password"]
    EXCEPTIONS = [BadRequest, InvalidEmail, InvalidUsername, UserAlreadyExists]

    walter_db: WalterDB
    send_verify_email: SendVerifyEmail

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
        walter_ses: WalterSESClient,
        template_engine: TemplatesEngine,
        templates_bucket: TemplatesBucket,
    ) -> None:
        super().__init__(
            CreateUser.API_NAME,
            CreateUser.REQUIRED_QUERY_FIELDS,
            CreateUser.REQUIRED_HEADERS,
            CreateUser.REQUIRED_FIELDS,
            CreateUser.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db
        self.send_verify_email = SendVerifyEmail(
            walter_authenticator,
            walter_cw,
            walter_db,
            walter_ses,
            template_engine,
            templates_bucket,
        )

    def execute(self, event: dict, authenticated_email: str = None) -> dict:
        self._create_new_user(event)
        self._send_verification_email(event)
        return self._create_response(
            http_status=HTTPStatus.CREATED,
            status=Status.SUCCESS,
            message="User created!",
        )

    def validate_fields(self, event: dict) -> None:
        body = json.loads(event["body"])
        email = body[
            "email"
        ].lower()  # lowercase email for case-insensitive matching for login
        username = body["username"]
        self._verify_email(email)
        self._verify_username(username)
        self._verify_user_does_not_already_exist(email)

    def is_authenticated_api(self) -> bool:
        return False

    def _verify_email(self, email: str) -> None:
        log.info(f"Validating email: '{email}'")
        if not is_valid_email(email):
            raise InvalidEmail("Invalid email!")
        log.info("Successfully validated email!")

    def _verify_username(self, username: str) -> None:
        log.info(f"Validating username: '{username}'")
        if not is_valid_username(username):
            raise InvalidUsername("Invalid username!")
        log.info("Successfully validated username!")

    def _verify_user_does_not_already_exist(self, email: str) -> None:
        log.info(f"Validate user does not already exist with email: '{email}'")
        user = self.walter_db.get_user(email)
        if user is not None:
            raise UserAlreadyExists("User already exists!")
        log.info("Successfully validated that user does not already exist!")

    def _create_new_user(self, event: dict) -> None:
        log.info("Creating new user")
        body = json.loads(event["body"])
        email = body[
            "email"
        ].lower()  # store the user email as lower-case for case-insensitive matching
        self.walter_db.create_user(
            email=email,
            username=body["username"],
            password=body["password"],
        )

    def _send_verification_email(self, event: dict) -> None:
        log.info("Sending verification email to user")

        # generate token for user to send verification email
        body = json.loads(event["body"])
        email = body["email"].lower()  # lower-case email for case-insensitive matching
        token = self.authenticator.generate_user_token(email)

        event["headers"]["Authorization"] = f"Bearer {token}"
        self.send_verify_email.invoke(event)
