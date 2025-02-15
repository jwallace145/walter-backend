import datetime as dt
import json
from dataclasses import dataclass

from src.api.common.exceptions import UserDoesNotExist, InvalidPassword, InvalidEmail
from src.api.common.methods import WalterAPIMethod, HTTPStatus, Status
from src.api.common.utils import is_valid_email
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.database.users.models import User
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class AuthUser(WalterAPIMethod):
    """
    AuthUser

    Validate the given password against the stored hash for the given user email.
    If the password is correct, return a unique identity token for the user to
    use to make authenticated requests.
    """

    API_NAME = "AuthUser"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"content-type": "application/json"}
    REQUIRED_FIELDS = ["email", "password"]
    EXCEPTIONS = [UserDoesNotExist, InvalidPassword, InvalidEmail]

    walter_db: WalterDB
    walter_sm: WalterSecretsManagerClient

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
        walter_sm: WalterSecretsManagerClient,
    ) -> None:
        super().__init__(
            AuthUser.API_NAME,
            AuthUser.REQUIRED_QUERY_FIELDS,
            AuthUser.REQUIRED_HEADERS,
            AuthUser.REQUIRED_FIELDS,
            AuthUser.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db
        self.walter_sm = walter_sm

    def execute(self, event: dict, authenticated_email: str = None) -> dict:
        user = self._verify_user_exists(event)
        self._verify_password(event, user)
        self._update_last_active_date(user)
        token = self.authenticator.generate_user_token(user.email)
        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="User authenticated!",
            data={"token": token},
        )

    def validate_fields(self, event: dict) -> None:
        body = json.loads(event["body"])

        # verify email is valid
        email = body["email"].lower()
        if not is_valid_email(email):
            raise InvalidEmail("Invalid email!")

    def is_authenticated_api(self) -> bool:
        return False

    def _verify_user_exists(self, event: dict) -> User:
        email = json.loads(event["body"])["email"].lower()
        log.info(f"Verifying user exists with email '{email}'")
        user = self.walter_db.get_user(email)
        if user is None:
            raise UserDoesNotExist("User not found!")
        log.info("Verified user exists!")
        return user

    def _verify_password(self, event: dict, user: User) -> None:
        log.info("Verifying password matches stored password hash")
        password = json.loads(event["body"])["password"]
        if not self.authenticator.check_password(password, user.password_hash):
            raise InvalidPassword("Password incorrect!")
        log.info("Verified password matches!")

    def _update_last_active_date(self, user: User) -> None:
        log.info("Updating user last active time")
        user.last_active_date = dt.datetime.now(dt.UTC)
        self.walter_db.update_user(user)
