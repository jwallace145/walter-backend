from dataclasses import dataclass
from typing import List

from src.database.users.models import User
from src.aws.s3.client import WalterS3Client
from src.environment import Domain
from src.utils.log import Logger
from datetime import datetime as dt

log = Logger(__name__).get_logger()


@dataclass
class NewslettersBucket:
    """
    Newsletters S3 Bucket

    This bucket contains the email dumps Walter sends to subscribers every day.
    The contents of the dumps are organized by date and then user and template.
    """

    BUCKET = "walterai-newsletters-{domain}"

    NEWSLETTERS_DIR = "newsletters"
    NEWSLETTER_KEY = "{newsletters_dir}/{user}/{date}/{template}/index.html"
    USER_NEWSLETTERS_PREFIX = "{newsletters_dir}/{user}/"

    client: WalterS3Client
    domain: Domain

    bucket: str = None  # set during post init

    def __post_init__(self) -> None:
        self.bucket = NewslettersBucket._get_bucket_name(self.domain)
        log.debug(
            f"Creating '{self.domain.value}' NewslettersBucket S3 client with bucket '{self.bucket}'"
        )

    def put_newsletter(self, user: User, template: str, contents: str) -> None:
        """Write newsletter to S3.

        This method writes a newsletter generated for a user to S3.

        Args:
            user (User): The user to send the newsletter.
            template (str): The name of the template.
            contents (str): The contents of the template to put to S3.
        """
        log.info("Dumping newsletter to archive...")
        key = NewslettersBucket._get_newsletter_key(
            user, template, dt.now().replace(hour=0, minute=0, second=0, microsecond=0)
        )
        self.client.put_object(self.bucket, key, contents)

    def get_newsletter(self, user: User, date: dt) -> str:
        log.info(
            f"Getting '{date.strftime('%Y-%m-%d')}' newsletter from archive for user '{user.username}'"
        )
        prefix = NewslettersBucket._get_user_newsletters_prefix(user) + date.strftime(
            "y=%Y/m=%m/d=%d/"
        )
        keys = self.client.list_objects(self.bucket, prefix)
        if len(keys) == 0:
            log.info(
                f"No newsletter found in archive for user '{user.username}' and date '{date.strftime('%Y-%m-%d')}'!"
            )
            return None
        log.info(f"Returned {len(keys)} newsletters from archive for user and date!")
        return self.client.get_object(self.bucket, keys[0])

    def get_user_newsletters(self, user: User) -> List[str]:
        """
        Get newsletters sent to user from archive.

        Args:
            user: The user that received the newsletters.

        Returns:
            The keys of the newsletters sent to the user.
        """
        log.info(f"Getting newsletters for user '{user.username}'")
        prefix = NewslettersBucket._get_user_newsletters_prefix(user)
        keys = self.client.list_objects(self.bucket, prefix)
        if len(keys) == 0:
            log.info(f"No newsletters found in archive for user '{user.username}'!")
        else:
            log.info(f"Returned {len(keys)} newsletters from archive for user!")
        return keys

    @staticmethod
    def _get_bucket_name(domain: Domain) -> str:
        return NewslettersBucket.BUCKET.format(domain=domain.value)

    @staticmethod
    def _get_newsletter_key(user: User, template: str, date: dt) -> str:
        return NewslettersBucket.NEWSLETTER_KEY.format(
            newsletters_dir=NewslettersBucket.NEWSLETTERS_DIR,
            user=user.username.lower(),
            date=dt.strftime(
                date,
                "y=%Y/m=%m/d=%d",
            ),
            template=template,
        )

    @staticmethod
    def _get_user_newsletters_prefix(user: User) -> str:
        return NewslettersBucket.USER_NEWSLETTERS_PREFIX.format(
            newsletters_dir=NewslettersBucket.NEWSLETTERS_DIR,
            user=user.username.lower(),
        )
