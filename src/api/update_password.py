import json
from dataclasses import dataclass

from src.api.common.exceptions import (
    BadRequest,
    NotAuthenticated,
    InvalidPassword,
    UserDoesNotExist,
)
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import Response, HTTPStatus, Status
from src.api.common.utils import is_valid_password
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.database.users.models import User

from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class UpdatePassword(WalterAPIMethod):
    """
    WalterAPI: UpdatePassword

    This API updates a user's password given a valid authentication token.
    This implies the user is either currently logged in and forget their password
    and is proactively updating it or the user is just changing their password for
    added security. This API differs from the ChangePassword API in that the
    ChangePassword API uses an email authentication token to change their password.
    """

    API_NAME = "UpdatePassword"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer", "content-type": "application/json"}
    REQUIRED_FIELDS = ["current_password", "new_password"]
    EXCEPTIONS = [BadRequest, NotAuthenticated, InvalidPassword]

    walter_db: WalterDB

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
    ) -> None:
        super().__init__(
            UpdatePassword.API_NAME,
            UpdatePassword.REQUIRED_QUERY_FIELDS,
            UpdatePassword.REQUIRED_HEADERS,
            UpdatePassword.REQUIRED_FIELDS,
            UpdatePassword.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db

    def execute(self, event: dict, authenticated_email: str) -> Response:
        user = self._verify_user_exists(authenticated_email)

        # validate current password
        body = json.loads(event["body"])
        current_password = body["current_password"]
        if not self.authenticator.check_password(current_password, user.password_hash):
            return Response(
                api_name=UpdatePassword.API_NAME,
                http_status=HTTPStatus.OK,
                status=Status.FAILURE,
                message="Incorrect current password!",
            )

        # update user password in db
        new_password = body["new_password"]
        self._update_user_password(user, new_password)

        # TODO: Send did you just update password email to user...

        return Response(
            api_name=UpdatePassword.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Password updated successfully!",
        )

    def validate_fields(self, event: dict) -> None:
        body = json.loads(event["body"])
        new_password = body["new_password"]
        self._verify_new_password(new_password)

    def is_authenticated_api(self) -> bool:
        return True

    def _verify_new_password(self, new_password: str) -> None:
        log.info("Validating new password...")
        if not is_valid_password(new_password):
            raise InvalidPassword("Invalid new password!")
        log.info("Successfully validated new password!")

    def _verify_user_exists(self, email: str) -> User:
        log.info(f"Verifying user exists with email '{email}'")
        user = self.walter_db.get_user_by_email(email)
        if user is None:
            raise UserDoesNotExist(f"User does not exist with email '{email}'!")
        log.info("Verified user exists!")
        return user

    def _update_user_password(self, user: User, new_password: str) -> None:
        log.info(f"Updating user password for user '{user.email}'...")
        salt, new_password_hash = self.authenticator.hash_password(new_password)
        self.walter_db.update_user_password(user.email, new_password_hash)
        log.info(f"Successfully updated user password for user '{user.email}'!")
