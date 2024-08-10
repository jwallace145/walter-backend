from dataclasses import dataclass

from mypy_boto3_s3 import S3Client
from src.environment import Domain
from src.utils.log import Logger


log = Logger(__name__).get_logger()


@dataclass
class S3Client:
    """
    Walter AI S3 Client

    Buckets
        - "walterai-reports-{domain}"
    """

    REPORTS_BUCKET_NAME_FORMAT = "walterai-reports-{domain}"
    TEMPLATES_DIR = "templates"
    DEFAULT_TEMPLATE = "default"
    TEMPLATE_SPEC = "templatespec.yml"
    TEMPLATE = "template.jinja"
    NEWSLETTERS_DIR = "newsletters"
    NEWSLETTER = "index.html"

    client: S3Client
    domain: Domain

    bucket: str = None

    def __post_init__(self) -> None:
        log.debug(
            f"Creating {self.domain.value} S3 client in region '{self.client.meta.region_name}'"
        )
        self.bucket = S3Client._get_reports_bucket_name(self.domain)

    def get_template_spec(self, template_name: str = DEFAULT_TEMPLATE) -> None:
        key = S3Client._get_template_spec_key(template_name)
        log.info(f"Getting template spec from bucket '{self.bucket}' with key '{key}'")
        return self.get_object(key)

    def get_template(self, template_name: str = DEFAULT_TEMPLATE) -> None:
        key = S3Client._get_template_key(template_name)
        log.info(f"Getting template from bucket '{self.bucket}' with key '{key}'")
        return self.get_object(key)

    def get_object(self, key: str) -> str:
        return (
            self.client.get_object(Bucket=self.bucket, Key=key)["Body"]
            .read()
            .decode("utf-8")
        )

    def put_newsletter(self, template: str, contents: str) -> None:
        key = S3Client._get_newsletter_key(template)
        log.info(f"Dumping newsletter to bucket '{self.bucket}' with key '{key}'")
        self.put_object(key, contents)

    def put_object(self, key: str, contents: str) -> None:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=contents)

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
