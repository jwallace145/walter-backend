import re
from dataclasses import dataclass
from datetime import datetime as dt

from src.aws.s3.client import WalterS3Client
from src.environment import Domain
from src.news.models import NewsSummary
from src.utils.log import Logger

log = Logger(__name__).get_logger()

TODAY = dt.now().replace(hour=0, minute=0, second=0, microsecond=0)
"""(datetime): The current date which is used as the default value to get/write news summaries to/from S3."""


@dataclass
class NewsSummariesBucket:
    """
    News Summaries S3 Bucket
    """

    BUCKET = "walterai-news-summaries-{domain}"

    SUMMARIES_DIR = "summaries"
    SUMMARIES_PREFIX = "{summaries_dir}/{stock}"
    SUMMARY_KEY = "{summaries_dir}/{stock}/{date}/summary.html"

    client: WalterS3Client
    domain: Domain

    bucket: str = None  # set during post init

    def __post_init__(self) -> None:
        self.bucket = NewsSummariesBucket._get_bucket_name(self.domain)
        log.debug(
            f"Creating '{self.domain.value}' NewsSummariesBucket S3 client with bucket '{self.bucket}'"
        )

    def put_news_summary(self, stock: str, summary: str, date: dt = TODAY) -> None:
        log.info("Dumping news summary to S3")
        key = NewsSummariesBucket._get_summary_key(stock, date)
        return self.client.put_object(self.bucket, key, summary)

    def get_news_summary(self, stock: str, date: dt = TODAY) -> str | None:
        log.info(f"Getting news summary from archive for stock '{stock}' with date: '{date.isoformat()}'")
        key = NewsSummariesBucket._get_summary_key(stock, date)
        return self.client.get_object(self.bucket, key)

    def get_latest_news_summary(self, stock: str) -> NewsSummary | None:
        log.info(f"Getting latest news summary for stock '{stock}'")
        prefix = NewsSummariesBucket._get_summaries_prefix(stock)
        prefixes = self.client.list_objects(self.bucket, prefix)

        # ensure summaries exist for given stock
        if len(prefixes) == 0:
            log.info("No summaries found for stock '{stock}'!")
            return None

        summary = self.client.get_object(self.bucket, prefixes[-1])

        return NewsSummary(
            stock=stock.upper(),
            model_name="TODO",
            articles=[],
            summary=self.remove_non_alphanumeric(summary),
        )

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
    def _get_summaries_prefix(stock: str) -> str:
        return NewsSummariesBucket.SUMMARIES_PREFIX.format(
            summaries_dir=NewsSummariesBucket.SUMMARIES_DIR,
            stock=stock.upper(),
        )

    @staticmethod
    def _get_datestamp(timestamp: dt) -> str:
        return dt.strftime(
            timestamp.replace(hour=0, minute=0, second=0, microsecond=0),
            "y=%Y/m=%m/d=%d",
        )

    def remove_non_alphanumeric(self, text: str) -> str:
        return re.sub(r"[^a-zA-Z0-9 ]", "", text)
