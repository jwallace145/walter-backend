from dataclasses import dataclass
from datetime import datetime

from src.api.common.exceptions import (
    NotAuthenticated,
    BadRequest,
    UserDoesNotExist,
    NewsletterDoesNotExist,
)
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.database.users.models import User
from src.newsletters.client import NewslettersBucket
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class GetNewsletter(WalterAPIMethod):
    """
    WalterAPI: GetNewsletter
    """

    DATE_QUERY_FIELD_FORMAT = "%Y-%m-%d"

    API_NAME = "GetNewsletter"
    REQUIRED_QUERY_FIELDS = ["date"]
    REQUIRED_HEADERS = {"Authorization": "Bearer"}
    REQUIRED_FIELDS = []
    EXCEPTIONS = [
        BadRequest,
        NotAuthenticated,
        UserDoesNotExist,
        NewsletterDoesNotExist,
    ]

    walter_db: WalterDB
    newsletters_archive: NewslettersBucket

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
        newsletters_archive: NewslettersBucket,
    ) -> None:
        super().__init__(
            GetNewsletter.API_NAME,
            GetNewsletter.REQUIRED_QUERY_FIELDS,
            GetNewsletter.REQUIRED_HEADERS,
            GetNewsletter.REQUIRED_FIELDS,
            GetNewsletter.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db
        self.newsletters_archive = newsletters_archive

    def execute(self, event: dict, authenticated_email: str = None) -> dict:
        user = self._verify_user_exists(authenticated_email)
        date = self._get_date(event)
        newsletter = self._get_newsletter_from_archive(user, date)
        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Successfully retrieved newsletter!",
            data={"newsletter": newsletter},
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True

    def _verify_user_exists(self, email: str) -> User:
        log.info(f"Verifying user exists with '{email}'")
        user = self.walter_db.get_user(email)
        if user is None:
            raise UserDoesNotExist("User does not exist!")
        log.info("Verified user exists!")
        return user

    def _get_date(self, event: dict) -> datetime:
        date_str = event["queryStringParameters"]["date"]
        return datetime.strptime(date_str, GetNewsletter.DATE_QUERY_FIELD_FORMAT)

    def _get_newsletter_from_archive(self, user: User, date: datetime) -> str:
        log.info("Getting user newsletter from archive...")
        newsletter = self.newsletters_archive.get_newsletter(user, date)
        # TODO: Use a more specific exception
        if not newsletter:
            raise BadRequest("Newsletter not found!")
        log.info("Successfully retrieved user newsletter from archive!")
        return newsletter
