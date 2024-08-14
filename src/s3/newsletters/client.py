from dataclasses import dataclass

from src.dynamodb.models import User
from src.s3.client import WalterS3Client
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
    NEWSLETTER_KEY = "{newsletters_dir}/{date}/{user}/{template}/index.html"

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
            template (str): The name of the template.
            contents (str): The contents of the template to put to S3.
        """
        key = NewslettersBucket._get_newsletter_key(user, template)
        log.info(
            f"Dumping newsletter to S3 with URI '{WalterS3Client.get_uri(self.bucket, key)}'"
        )
        self.client.put_object(self.bucket, key, contents)

    @staticmethod
    def _get_bucket_name(domain: Domain) -> str:
        return NewslettersBucket.BUCKET.format(domain=domain.value)

    @staticmethod
    def _get_newsletter_key(user: User, template: str) -> str:
        return NewslettersBucket.NEWSLETTER_KEY.format(
            newsletters_dir=NewslettersBucket.NEWSLETTERS_DIR,
            date=dt.strftime(
                dt.now().replace(hour=0, minute=0, second=0, microsecond=0),
                "y=%Y/m=%m/d=%d",
            ),
            user=user.username,
            template=template,
        )
