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

    client: S3Client
    domain: Domain

    bucket: str = None

    def __post_init__(self) -> None:
        log.debug(
            f"Creating {self.domain.value} S3 client in region '{self.client.meta.region_name}'"
        )
        self.bucket = self._get_reports_bucket_name(self.domain)

    def put_report(self) -> None:
        pass

    def _get_reports_bucket_name(self, domain: Domain) -> str:
        return S3Client.REPORTS_BUCKET_NAME_FORMAT.format(domain=domain.value)
