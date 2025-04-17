import json
from dataclasses import dataclass
from datetime import datetime as dt
from typing import List

from src.aws.s3.client import WalterS3Client
from src.database.users.models import User
from src.environment import Domain
from src.newsletters.models import NewsletterMetadata
from src.templates.models import SupportedTemplate, get_supported_template
from src.utils.log import Logger

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
    NEWSLETTER_METADATA_KEY = "{newsletters_dir}/{user}/{date}/metadata.json"
    NEWSLETTER_KEY = "{newsletters_dir}/{user}/{date}/newsletter.html"
    USER_NEWSLETTERS_PREFIX = "{newsletters_dir}/{user}/"

    client: WalterS3Client
    domain: Domain

    bucket: str = None  # set during post init

    def __post_init__(self) -> None:
        self.bucket = NewslettersBucket._get_bucket_name(self.domain)
        log.debug(
            f"Creating '{self.domain.value}' NewslettersBucket S3 client with bucket '{self.bucket}'"
        )

    def put_newsletter(
        self,
        user: User,
        title: str,
        template: SupportedTemplate,
        model: str,
        contents: str,
    ) -> None:
        """
        Write user newsletter to newsletter archive.

        This method archives newsletters sent to users in S3 along
        with metadata such as the template and model used to generate
        the newsletter.

        Args:
            user (User): The user recipient of the newsletter.
            title (str): The title of the newsletter.
            template (SupportedTemplate): The name of the template used to create the newsletter.
            model (WalterModel): The model used by Walter to generate the newsletter.
            contents (str): The newsletter HTML contents to archive.
        """
        log.info("Dumping newsletter and metadata to archive...")
        date = dt.now().replace(hour=0, minute=0, second=0, microsecond=0)
        metadata_key = NewslettersBucket._get_metadata_key(user, date)
        metadata = NewslettersBucket._get_metadata(title, date, model, template)
        newsletter_key = NewslettersBucket._get_newsletter_key(user, date)
        self.client.put_object(self.bucket, metadata_key, metadata)
        self.client.put_object(self.bucket, newsletter_key, contents)

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

    def get_newsletter_metadata(self, user: User, date: dt) -> NewsletterMetadata:
        log.info(
            f"Getting '{date.strftime('%Y-%m-%d')}' newsletter metadata from archive for user '{user.username}'"
        )
        newsletter_metadata_key = NewslettersBucket._get_metadata_key(user, date)
        metadata = json.loads(
            self.client.get_object(self.bucket, newsletter_metadata_key)
        )
        return NewsletterMetadata(
            title=metadata["title"],
            date=dt.strptime(metadata["date"], "%Y-%m-%d"),
            model=metadata["model"],
            template=get_supported_template(metadata["template"]),
        )

    def get_newsletter_keys_for_user(self, user: User) -> List[str]:
        """
        Get the keys of all the newsletters for a user in the archive.

        Args:
            user: The user recipient of the newsletters.

        Returns:
            The list of newsletter keys for all newsletters sent to the user.
        """
        log.info(f"Getting list of newsletter keys for '{user.username}'")

        # search keys by user newsletter key prefix
        prefix = NewslettersBucket._get_user_newsletters_prefix(user)
        keys = self.client.list_objects(self.bucket, prefix)

        if len(keys) == 0:
            log.info(f"No newsletters found in archive for user '{user.username}'!")
        else:
            # filter out metadata keys and only get the newsletter keys
            keys = [key for key in keys if "metadata" not in key]
            log.info(
                f"Found {len(keys)} newsletters in the archive for user '{user.username}'"
            )

        return keys

    @staticmethod
    def _get_bucket_name(domain: Domain) -> str:
        return NewslettersBucket.BUCKET.format(domain=domain.value)

    @staticmethod
    def _get_metadata(
        title: str, date: dt, model: str, template: SupportedTemplate
    ) -> str:
        return json.dumps(
            NewsletterMetadata(
                title=title.strip(), date=date, model=model, template=template
            ).to_dict()
        )

    @staticmethod
    def _get_metadata_key(user: User, date: dt) -> str:
        return NewslettersBucket.NEWSLETTER_METADATA_KEY.format(
            newsletters_dir=NewslettersBucket.NEWSLETTERS_DIR,
            user=user.username.lower(),
            date=dt.strftime(date, "y=%Y/m=%m/d=%d"),
        )

    @staticmethod
    def _get_newsletter_key(user: User, date: dt) -> str:
        return NewslettersBucket.NEWSLETTER_KEY.format(
            newsletters_dir=NewslettersBucket.NEWSLETTERS_DIR,
            user=user.username.lower(),
            date=dt.strftime(
                date,
                "y=%Y/m=%m/d=%d",
            ),
        )

    @staticmethod
    def _get_user_newsletters_prefix(user: User) -> str:
        return NewslettersBucket.USER_NEWSLETTERS_PREFIX.format(
            newsletters_dir=NewslettersBucket.NEWSLETTERS_DIR,
            user=user.username.lower(),
        )
