from dataclasses import dataclass

from src.api.common.exceptions import (
    UserDoesNotExist,
    InvalidEmail,
    NotAuthenticated,
    EmailNotVerified,
    EmailNotSubscribed,
)
from src.api.common.methods import HTTPStatus, Status
from src.api.common.methods import WalterAPIMethod
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.database.users.models import User
from src.newsletters.queue import NewsletterRequest, NewslettersQueue
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class SendNewsletter(WalterAPIMethod):

    API_NAME = "SendNewsletter"
    REQUIRED_HEADERS = {"Authorization": "Bearer"}
    REQUIRED_FIELDS = []
    EXCEPTIONS = [
        NotAuthenticated,
        InvalidEmail,
        UserDoesNotExist,
        EmailNotVerified,
        EmailNotSubscribed,
    ]

    walter_db: WalterDB
    newsletters_queue: NewslettersQueue
    walter_sm: WalterSecretsManagerClient

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
        newsletters_queue: NewslettersQueue,
        walter_sm: WalterSecretsManagerClient,
    ) -> None:
        super().__init__(
            SendNewsletter.API_NAME,
            SendNewsletter.REQUIRED_HEADERS,
            SendNewsletter.REQUIRED_FIELDS,
            SendNewsletter.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db
        self.newsletters_queue = newsletters_queue
        self.walter_sm = walter_sm

    def execute(self, event: dict, authenticated_email: str) -> dict:
        user = self._verify_user_exists(authenticated_email)
        self._verify_user_email_verified(user)
        self._verify_user_is_subscribed(user)
        self._send_newsletter(user.email)
        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Newsletter sent!",
        )

    def validate_fields(self, event: dict) -> None:
        return

    def is_authenticated_api(self) -> bool:
        return True

    def _verify_user_exists(self, email: str) -> User:
        log.info(f"Verifying user exists: '{email}'")
        user = self.walter_db.get_user(email)
        if user is None:
            raise UserDoesNotExist("User not found!")
        log.info("Verified user exists!")
        return user

    def _verify_user_email_verified(self, user: User) -> None:
        log.info(f"Verifying user email is verified: '{user.email}'")
        if not user.verified:
            raise EmailNotVerified("Email not verified!")
        log.info("User email is verified!")

    def _verify_user_is_subscribed(self, user: User) -> None:
        log.info(f"Verifying user is subscribed: '{user.email}'")
        if not user.subscribed:
            raise EmailNotSubscribed("Email not subscribed!")
        log.info("User email is subscribed!")

    def _send_newsletter(self, email: str) -> None:
        log.info(f"Adding newsletter message to queue for user: '{email}")
        self.newsletters_queue.add_newsletter_request(NewsletterRequest(email))
        log.info("Successfully added newsletter message to queue for user!")
