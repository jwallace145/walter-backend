import math
from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple

from src.api.common.exceptions import BadRequest, NotAuthenticated, UserDoesNotExist
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Status, Response
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.database.users.models import User
from src.newsletters.client import NewslettersBucket
from src.newsletters.models import NewsletterMetadata
from src.templates.models import get_supported_template_by_value
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class GetNewsletters(WalterAPIMethod):
    """
    WalterAPI: GetNewsletters

    Get the newsletters for a user from the archives. Walter
    generates and sends newsletters to users to keep them informed
    about their financial health and progress. This API retrieves
    the URIs of previously generated newsletters for the user.
    This API can be used in conjunction with the GetNewsletter
    API to retrieve the newsletter content.
    """

    PAGE_SIZE = 5

    API_NAME = "GetNewsletters"
    REQUIRED_QUERY_FIELDS = ["page"]
    REQUIRED_HEADERS = {"Authorization": "Bearer"}
    REQUIRED_FIELDS = []
    EXCEPTIONS = [BadRequest, NotAuthenticated, UserDoesNotExist]

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
            GetNewsletters.API_NAME,
            GetNewsletters.REQUIRED_QUERY_FIELDS,
            GetNewsletters.REQUIRED_HEADERS,
            GetNewsletters.REQUIRED_FIELDS,
            GetNewsletters.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db
        self.newsletters_archive = newsletters_archive

    def execute(self, event: dict, authenticated_email: str = None) -> Response:
        user = self._verify_user_exists(authenticated_email)
        newsletter_keys = self._get_newsletter_keys(user)
        page, last_page = self._verify_newsletters_page(event, len(newsletter_keys))
        newsletter_metadata = self._get_newsletter_metadata(user, newsletter_keys, page)
        data = self._get_newsletters_response_data(newsletter_metadata, page, last_page)
        return Response(
            api_name=GetNewsletters.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Successfully retrieved newsletters!",
            data=data,
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

    def _get_newsletter_keys(self, user: User) -> List[str]:
        log.info(f"Getting newsletter keys from archive for user '{user.email}'")
        # sort newsletter keys in reverse order to ensure results are
        # chronologically descending order
        return sorted(
            self.newsletters_archive.get_newsletter_keys_for_user(user), reverse=True
        )

    def _verify_newsletters_page(
        self, event: dict, num_newsletters: int
    ) -> Tuple[int, int]:
        log.info("Verifying newsletters page is valid...")

        page = int(WalterAPIMethod.get_query_field(event, "page"))
        last_page = max(math.ceil(num_newsletters / GetNewsletters.PAGE_SIZE), 1)

        if page < 1:
            log.error(f"Page {page} out of range! Page must be greater than 0!")
            raise BadRequest(f"Page {page} out of range! Page must be greater than 0!")

        if page > last_page:
            log.error(f"Page {page} out of range! Last page: {last_page}")
            raise BadRequest(f"Page {page} out of range! Last page: {last_page}")

        log.info("Verified newsletters page is valid!")
        return page, last_page

    def _get_newsletter_metadata(
        self, user: User, newsletter_keys: List[str], page: int
    ) -> List[NewsletterMetadata]:
        log.info(f"Getting newsletter metadata for user '{user.email}' from archive")

        metadata = []
        for newsletter_key in newsletter_keys:
            date = datetime.strptime(
                "".join(newsletter_key.split("/")[2:5]), "y=%Ym=%md=%d"
            )
            metadata.append(
                self.newsletters_archive.get_newsletter_metadata(user, date)
            )

        return metadata

    def _get_newsletters_response_data(
        self, newsletter_metadata: List[NewsletterMetadata], page: int, last_page: int
    ) -> dict:
        # get newsletters page from page index
        newsletters_page = newsletter_metadata[
            (page - 1) * GetNewsletters.PAGE_SIZE : (page * GetNewsletters.PAGE_SIZE)
        ]

        return {
            "current_page": page,
            "last_page": last_page,
            "newsletters": [newsletter.to_dict() for newsletter in newsletters_page],
        }

    @staticmethod
    def _get_newsletter_details(newsletter_key: str) -> dict:
        split_newsletter_key = newsletter_key.split("/")
        date = "/".join(split_newsletter_key[2:5])
        datestamp = datetime.strptime(date, "y=%Y/m=%m/d=%d")
        template = split_newsletter_key[5]
        return {
            "newsletter_key": newsletter_key,
            "datestamp": datetime.strftime(datestamp, "%Y-%m-%d"),
            "template": get_supported_template_by_value(template).name,
        }
