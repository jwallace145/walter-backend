import json
from dataclasses import dataclass

from src.api.exceptions import UserDoesNotExist, InvalidEmail, NotAuthenticated
from src.api.methods import WalterAPIMethod
from src.api.models import HTTPStatus, Status
from src.api.utils import is_valid_email
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.newsletters.queue import NewsletterRequest, NewslettersQueue
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class SendNewsletter(WalterAPIMethod):

    API_NAME = "SendNewsletter"
    REQUIRED_FIELDS = ["email"]
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

    def execute(self, event: dict) -> dict:
        body = json.loads(event["body"])

        email = body["email"]
        user = self.walter_db.get_user(email)
        if user is None:
            raise UserDoesNotExist("User not found!")

        self.newsletters_queue.add_newsletter_request(NewsletterRequest(email))

        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Newsletter sent!",
        )

    def validate_fields(self, event: dict) -> None:
        body = json.loads(event["body"])
        email = body["email"]

        if not is_valid_email(email):
            raise InvalidEmail("Invalid email!")

    def is_authenticated_api(self) -> bool:
        return True

    def get_jwt_secret_key(self) -> str:
        return self.walter_sm.get_jwt_secret_key()
