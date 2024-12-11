from src.api.common.exceptions import (
    BadRequest,
    NotAuthenticated,
    EmailAlreadyVerified,
    UserDoesNotExist,
)
from dataclasses import dataclass
from src.api.common.methods import WalterAPIMethod, HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.database.users.models import User
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class VerifyEmail(WalterAPIMethod):
    """
    WalterAPI - VerifyEmail
    """

    API_NAME = "VerifyEmail"
    REQUIRED_HEADERS = [
        {"Authorization": "Bearer"},
    ]
    REQUIRED_FIELDS = []
    EXCEPTIONS = [BadRequest, NotAuthenticated, UserDoesNotExist, EmailAlreadyVerified]

    walter_db: WalterDB

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
    ) -> None:
        super().__init__(
            VerifyEmail.API_NAME,
            VerifyEmail.REQUIRED_FIELDS,
            VerifyEmail.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db

    def execute(self, event: dict, authenticated_email: str = None) -> dict:
        token = self.authenticator.get_token(event)
        email = self._validate_token(token)
        user = self._verify_user_exists(email)
        self.walter_db.verify_user(user)
        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Successfully verified email!",
        )

    def validate_fields(self, event: dict) -> None:
        pass  # no payload

    def is_authenticated_api(self) -> bool:
        return False

    def _validate_token(self, token: str) -> str:
        log.info("Validating email verification token")
        if token is None:
            raise NotAuthenticated("Not authenticated!")

        decoded_token = self.authenticator.decode_email_token(token)
        if decoded_token is None:
            raise NotAuthenticated("Not authenticated!")

        email = decoded_token["sub"]
        log.info(f"Validated email verification token for user email: '{email}'")
        return email

    def _verify_user_exists(self, email: str) -> User:
        log.info(f"Verifying user exists with email: '{email}'")
        user = self.walter_db.get_user(email)
        if user is None:
            raise UserDoesNotExist("User does not exist!")
        log.info("Verified user exists!")
        return user
