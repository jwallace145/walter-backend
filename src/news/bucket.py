from dataclasses import dataclass
from datetime import datetime as dt

from src.aws.s3.client import WalterS3Client
from src.environment import Domain
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class NewsSummariesBucket:
    """
    News Summaries S3 Bucket
    """

    BUCKET = "walterai-news-summaries-{domain}"

    SUMMARIES_DIR = "summaries"
    SUMMARY_KEY = "{summaries_dir}/{stock}/{date}/summary.html"

    client: WalterS3Client
    domain: Domain

    bucket: str = None  # set during post init

    def __post_init__(self) -> None:
        self.bucket = NewsSummariesBucket._get_bucket_name(self.domain)
        log.debug(
            f"Creating '{self.domain.value}' NewsSummariesBucket S3 client with bucket '{self.bucket}'"
        )

    def put_news_summary(self, stock: str, summary: str) -> None:
        log.info("Dumping news summary to S3")
        key = NewsSummariesBucket._get_summary_key(stock, dt.now())
        self.client.put_object(self.bucket, key, summary)

    def get_news_summary(self, stock: str) -> str | None:
        log.info("Getting news summary from S3")
        key = NewsSummariesBucket._get_summary_key(stock, dt.now())
        return self.client.get_object(self.bucket, key)

    @staticmethod
    def _get_bucket_name(domain: Domain) -> str:
        return NewsSummariesBucket.BUCKET.format(domain=domain.value)

    @staticmethod
    def _get_summary_key(stock: str, timestamp: dt) -> str:
        return NewsSummariesBucket.SUMMARY_KEY.format(
            summaries_dir=NewsSummariesBucket.SUMMARIES_DIR,
            stock=stock.upper(),
            date=NewsSummariesBucket._get_datestamp(timestamp),
        )

    @staticmethod
    def _get_datestamp(timestamp: dt) -> str:
        return dt.strftime(
            timestamp.replace(hour=0, minute=0, second=0, microsecond=0),
            "y=%Y/m=%m/d=%d",
        )
