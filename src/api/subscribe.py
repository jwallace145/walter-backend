from src.api.common.exceptions import NotAuthenticated, UserDoesNotExist
from src.api.common.methods import WalterAPIMethod, HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.database.users.models import User

from src.utils.log import Logger

log = Logger(__name__).get_logger()


class Subscribe(WalterAPIMethod):
    """
    WalterAPI - Subscribe
    """

    API_NAME = "Subscribe"
    REQUIRED_FIELDS = []
    EXCEPTIONS = [NotAuthenticated, UserDoesNotExist]

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
    ) -> None:
        super().__init__(
            Subscribe.API_NAME,
            Subscribe.REQUIRED_FIELDS,
            Subscribe.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db

    def execute(self, event: dict, authenticated_email: str) -> dict:
        user = self._verify_user_exists(authenticated_email)
        self._update_user_subscribed_status(user)
        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Subscribed user!",
        )

    def validate_fields(self, event: dict) -> None:
        pass  # no payload for subscribe request

    def is_authenticated_api(self) -> bool:
        return True

    def _verify_user_exists(self, authenticated_email: str) -> User:
        log.info(f"Verifying user exists: '{authenticated_email}'")
        user = self.walter_db.get_user(authenticated_email)
        if user is None:
            raise UserDoesNotExist("User does not exist!")
        log.info("Verified user exists!")
        return user

    def _update_user_subscribed_status(self, user: User) -> None:
        log.info("Updating user subscribed status to true")
        user.subscribed = True
        self.walter_db.update_user(user)
        log.info("Successfully updated user subscribed status to true!")
