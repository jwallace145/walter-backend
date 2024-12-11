import json

from dataclasses import dataclass
from src.api.common.exceptions import BadRequest, NotAuthenticated
from src.api.common.methods import WalterAPIMethod, HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class ChangePassword(WalterAPIMethod):
    """
    WalterAPI - ChangePassword

    Change the user's stored password hash.
    """

    API_NAME = "ChangePassword"
    REQUIRED_HEADERS = [
        {"Authorization": "Bearer"},
        {"content-type": "application/json"},
    ]
    REQUIRED_FIELDS = ["new_password"]
    EXCEPTIONS = [BadRequest, NotAuthenticated]

    walter_db: WalterDB

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
    ) -> None:
        super().__init__(
            ChangePassword.API_NAME,
            ChangePassword.REQUIRED_HEADERS,
            ChangePassword.REQUIRED_FIELDS,
            ChangePassword.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db

    def execute(self, event: dict, authenticated_email: str = None) -> dict:
        email = self._validate_token(event)
        self._update_user_password(email, event)
        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Successfully changed password!",
        )

    def validate_fields(self, event: dict) -> None:
        pass  # no additional validations

    def is_authenticated_api(self) -> bool:
        return False

    def _validate_token(self, event: dict) -> str:
        log.info("Validating token")

        # ensure token is not null
        token = self.authenticator.get_token(event)
        if token is None:
            raise NotAuthenticated("Not authenticated!")

        # ensure token is valid
        decoded_token = self.authenticator.decode_change_password_token(token)
        if decoded_token is None:
            raise NotAuthenticated("Not authenticated!")

        log.info("Successfully validated token!")

        return decoded_token["sub"]

    def _update_user_password(self, email: str, event: dict) -> None:
        log.info(f"Updating user password for user email: '{email}'")

        # hash new password
        body = json.loads(event["body"])
        new_password = body["new_password"]
        salt, new_password_hash = self.authenticator.hash_password(new_password)

        self.walter_db.update_user_password(
            email=email, password_hash=new_password_hash
        )
        log.info("Successfully updated user password!")
