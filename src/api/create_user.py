import json

from src.api.exceptions import (
    InvalidEmail,
    InvalidUsername,
    UserAlreadyExists,
    BadRequest,
)
from src.api.methods import HTTPStatus, Status
from src.api.methods import WalterAPIMethod
from src.api.methods import is_valid_username, is_valid_email
from src.api.send_verify_email import SendVerifyEmail
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.ses.client import WalterSESClient
from src.database.client import WalterDB
from src.templates.bucket import TemplatesBucket
from src.templates.engine import TemplatesEngine
from src.utils.log import Logger

log = Logger(__name__).get_logger()


class CreateUser(WalterAPIMethod):
    """
    WalterAPI - CreateUser
    """

    API_NAME = "CreateUser"
    REQUIRED_FIELDS = ["email", "username", "password"]
    EXCEPTIONS = [BadRequest, InvalidEmail, InvalidUsername, UserAlreadyExists]

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
        body = json.loads(event["body"])

        # create user and add to db
        self.walter_db.create_user(
            email=body["email"],
            username=body["username"],
            password=body["password"],
        )

        # generate token for user to send verification email
        token = self.authenticator.generate_user_token(body["email"])

        # invoke send verify email api and send email verification email to new user
        event["headers"]["Authorization"] = f"Bearer {token}"
        self.send_verify_email.invoke(event)

        # return successful response
        return self._create_response(
            http_status=HTTPStatus.CREATED,
            status=Status.SUCCESS,
            message="User created!",
        )

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

    def is_valid_username(self, username: str) -> bool:
        return username.isalnum()
