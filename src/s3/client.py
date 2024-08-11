from dataclasses import dataclass
from io import BytesIO
from typing import Dict

from mypy_boto3_s3 import S3Client
from src.environment import Domain
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class S3Client:
    """
    S3 Client

    This client is responsible for getting templates from S3 and
    writing rendered templates to S3 before sending to users.

    Buckets
        - "walterai-reports-{domain}" # TODO: Create a new bucket for email dumps
    """

    REPORTS_BUCKET_NAME_FORMAT = "walterai-reports-{domain}"
    TEMPLATES_DIR = "templates"
    ASSETS_DIR = "images"
    NEWSLETTERS_DIR = "newsletters"

    DEFAULT_TEMPLATE = "default"
    TEMPLATE_SPEC = "templatespec.yml"
    TEMPLATE = "template.jinja"
    NEWSLETTER = "index.html"

    client: S3Client
    domain: Domain

    bucket: str = None

    def __post_init__(self) -> None:
        log.debug(
            f"Creating {self.domain.value} S3 client in region '{self.client.meta.region_name}'"
        )
        self.bucket = S3Client._get_reports_bucket_name(self.domain)

    def get_template_spec(self, template_name: str = DEFAULT_TEMPLATE) -> str:
        """Get template spec YAML config file from S3.

        This method gets the template spec YAML config file from S3 for the given template.
        The template spec file contains the template keys and prompts to use to successfully
        render the template.

        Args:
            template_name (str, optional): The name of the template to get the template spec.

        Returns:
            _type_: The template spec file.
        """
        key = S3Client._get_template_spec_key(template_name)
        log.info(f"Getting template spec from bucket '{self.bucket}' with key '{key}'")
        return self._get_object(key)

    def get_template(self, template_name: str = DEFAULT_TEMPLATE) -> str:
        """Get Jinja template from S3.

        This method gets the Jinja template from S3 for the given template. The Jinja template
        is utilized to render the user email with the AI responses to the intended prompts.
        Each template in S3 is required to have a Jinja template file.

        Args:
            template_name (str, optional): The name of the template to get the Jinja template.

        Returns:
            str: The Jinja template.
        """
        key = S3Client._get_template_key(template_name)
        log.info(f"Getting template from bucket '{self.bucket}' with key '{key}'")
        return self._get_object(key)

    def get_template_images(
        self, template_name: str = DEFAULT_TEMPLATE
    ) -> Dict[str, BytesIO]:
        """Get HTML template assets from S3.

        This method gets the template assets for the given template from S3 to include in the
        rendered email as attachments so that the generated emails can include media. Any
        template that uses media needs to have the required assets in S3.

        Args:
            template_name (str, optional): The name of the template to get assets from S3.

        Returns:
            Dict[str, BytesIO]: The name of the asset and the stream of it contents.
        """
        prefix = S3Client._get_assets_prefix(template_name)
        log.info(
            f"Getting assets for template '{template_name}' from bucket '{self.bucket}' with prefix '{prefix}'"
        )

        # get asset keys by listing all objects under asset prefix
        keys = [content["Key"] for content in self._list_objects(prefix)["Contents"]]

        # for each key get asset name and download object to memory
        assets = {}
        for key in keys:
            asset_name = key.split("/")[-1]

            # if asset name is empty skip, weird S3 list behavior
            if asset_name == "":
                continue

            assets[asset_name] = self._download_object(key)

        return assets

    def put_newsletter(self, template: str, contents: str) -> None:
        """Write newsletter to S3.

        This method writes a newsletter generated for a user to S3.

        Args:
            template (str): The name of the template.
            contents (str): The contents of the template to put to S3.
        """
        key = S3Client._get_newsletter_key(template)
        log.info(f"Dumping newsletter to bucket '{self.bucket}' with key '{key}'")
        self._put_object(key, contents)

    def _get_object(self, key: str) -> str:
        return (
            self.client.get_object(Bucket=self.bucket, Key=key)["Body"]
            .read()
            .decode("utf-8")
        )

    def _download_object(self, key: str) -> BytesIO:
        stream = BytesIO()
        self.client.download_fileobj(Bucket=self.bucket, Key=key, Fileobj=stream)
        return stream

    def _put_object(self, key: str, contents: str) -> None:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=contents)

    def _list_objects(self, prefix: str) -> None:
        return self.client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)

    @staticmethod
    def _get_reports_bucket_name(domain: Domain) -> str:
        return S3Client.REPORTS_BUCKET_NAME_FORMAT.format(domain=domain.value)

    @staticmethod
    def _get_template_spec_key(template_name: str) -> str:
        return f"{S3Client.TEMPLATES_DIR}/{template_name}/{S3Client.TEMPLATE_SPEC}"

    @staticmethod
    def _get_template_key(template_name: str) -> str:
        return f"{S3Client.TEMPLATES_DIR}/{template_name}/{S3Client.TEMPLATE}"

    @staticmethod
    def _get_newsletter_key(template_name: str) -> str:
        return f"{S3Client.NEWSLETTERS_DIR}/{template_name}/{S3Client.NEWSLETTER}"

    @staticmethod
    def _get_assets_prefix(template_name: str) -> str:
        return f"{S3Client.TEMPLATES_DIR}/{template_name}/{S3Client.ASSETS_DIR}/"
