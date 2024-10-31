from dataclasses import dataclass

from src.api.exceptions import UserDoesNotExist, InvalidEmail, NotAuthenticated
from src.api.methods import WalterAPIMethod
from src.api.methods import HTTPStatus, Status
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.newsletters.queue import NewsletterRequest, NewslettersQueue
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class SendNewsletter(WalterAPIMethod):

    API_NAME = "SendNewsletter"
    REQUIRED_FIELDS = []
    EXCEPTIONS = [NotAuthenticated, InvalidEmail, UserDoesNotExist]

    def __init__(
        self,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
        newsletters_queue: NewslettersQueue,
        walter_sm: WalterSecretsManagerClient,
    ) -> None:
        super().__init__(
            SendNewsletter.API_NAME,
            SendNewsletter.REQUIRED_FIELDS,
            SendNewsletter.EXCEPTIONS,
            walter_cw,
        )
        self.walter_db = walter_db
        self.newsletters_queue = newsletters_queue
        self.walter_sm = walter_sm

    def execute(self, event: dict, authenticated_email: str) -> dict:
        user = self.walter_db.get_user(authenticated_email)
        if user is None:
            raise UserDoesNotExist("User not found!")

        self.newsletters_queue.add_newsletter_request(
            NewsletterRequest(authenticated_email)
        )

        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Newsletter sent!",
        )

    def validate_fields(self, event: dict) -> None:
        return

    def is_authenticated_api(self) -> bool:
        return True

    def get_jwt_secret_key(self) -> str:
        return self.walter_sm.get_jwt_secret_key()
