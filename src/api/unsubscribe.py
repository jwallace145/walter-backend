from dataclasses import dataclass

from src.api.common.exceptions import (
    NotAuthenticated,
    UserDoesNotExist,
    EmailAlreadyUnsubscribed,
)
from src.api.common.methods import WalterAPIMethod, HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.database.users.models import User
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class Unsubscribe(WalterAPIMethod):
    """
    WalterAPI - Unsubscribe
    """

    API_NAME = "Unsubscribe"
    REQUIRED_HEADERS = {"Authorization": "Bearer"}
    REQUIRED_FIELDS = []
    EXCEPTIONS = [NotAuthenticated, UserDoesNotExist, EmailAlreadyUnsubscribed]

    walter_db: WalterDB

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
    ) -> None:
        super().__init__(
            Unsubscribe.API_NAME,
            Unsubscribe.REQUIRED_HEADERS,
            Unsubscribe.REQUIRED_FIELDS,
            Unsubscribe.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db

    def execute(self, event: dict, authenticated_email: str) -> dict:
        user = self._verify_user_exists(authenticated_email)
        self._verify_user_is_not_already_unsubscribed(user)
        self._unsubscribe_user(user)
        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Unsubscribed user!",
        )

    def validate_fields(self, event: dict) -> None:
        pass  # no payload for get user requests

    def is_authenticated_api(self) -> bool:
        return True

    def _verify_user_exists(self, email: str) -> User:
        log.info(f"Verifying user exists with email: '{email}'")
        user = self.walter_db.get_user(email)
        if user is None:
            raise UserDoesNotExist("User does not exist!")
        log.info("Verified user exists!")
        return user

    def _verify_user_is_not_already_unsubscribed(self, user: User) -> None:
        log.info(f"Verifying user is not already unsubscribed: '{user.email}'")
        if not user.subscribed:
            raise EmailAlreadyUnsubscribed("Email is already unsubscribed!")
        log.info("Verified user is not already unsubscribed!")

    def _unsubscribe_user(self, user: User) -> None:
        log.info(f"Unsubscribing user from newsletter with email: '{user.email}'")
        user.subscribed = False
        self.walter_db.update_user(user)
        log.info("Successfully unsubscribed user from newsletter!")
