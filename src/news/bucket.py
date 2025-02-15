import json
import re
from dataclasses import dataclass
from datetime import datetime as dt

from src.aws.s3.client import WalterS3Client
from src.environment import Domain
from src.summaries.models import NewsSummary
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
    METADATA_KEY = "{summaries_dir}/{stock}/{date}/metadata.json"
    SUMMARY_KEY = "{summaries_dir}/{stock}/{date}/summary.html"

    client: WalterS3Client
    domain: Domain

    bucket: str = None  # set during post init

    def __post_init__(self) -> None:
        self.bucket = NewsSummariesBucket._get_bucket_name(self.domain)
        log.debug(
            f"Creating '{self.domain.value}' NewsSummariesBucket S3 client with bucket '{self.bucket}'"
        )

    def put_news_summary(self, news: NewsSummary) -> str:
        log.info(
            f"Putting news summary to archive for stock '{news.stock}' with date: '{news.datestamp.strftime('%Y-%m-%d')}'"
        )

        log.debug(
            f"Putting news summary metadata to archive for stock '{news.stock}'..."
        )
        metadata = json.dumps(news.get_metadata(), indent=4)
        metadata_key = NewsSummariesBucket._get_metadata_key(news.stock, news.datestamp)
        self.client.put_object(self.bucket, metadata_key, metadata)

        log.debug(f"Putting news summary to archive for stock '{news.stock}'...")
        summary = news.summary
        summary_key = NewsSummariesBucket._get_summary_key(news.stock, news.datestamp)
        return self.client.put_object(self.bucket, summary_key, summary)

    def get_news_summary(self, stock: str, date: dt = TODAY) -> str | None:
        log.info(
            f"Getting news summary from archive for stock '{stock}' with date: '{date.strftime('%Y-%m-%d')}'..."
        )
        key = NewsSummariesBucket._get_summary_key(stock, date)
        return self.client.get_object(self.bucket, key)

    def get_latest_news_summary(self, stock: str) -> str | None:
        log.info(f"Getting latest news summary for stock '{stock}'")
        prefix = NewsSummariesBucket._get_summaries_prefix(stock)
        prefixes = self.client.list_objects(self.bucket, prefix)

        # ensure summaries exist for given stockpi
        if len(prefixes) == 0:
            log.info("No summaries found for stock '{stock}'!")
            return None

        summary = self.client.get_object(self.bucket, prefixes[-1])

        return self.remove_non_alphanumeric(summary)

    @staticmethod
    def _get_bucket_name(domain: Domain) -> str:
        return NewsSummariesBucket.BUCKET.format(domain=domain.value)

    @staticmethod
    def _get_metadata_key(stock: str, datestamp: dt):
        return NewsSummariesBucket.METADATA_KEY.format(
            summaries_dir=NewsSummariesBucket.SUMMARIES_DIR,
            stock=stock.upper(),
            date=NewsSummariesBucket._get_datestamp(datestamp),
        )

    @staticmethod
    def _get_summary_key(stock: str, datestamp: dt) -> str:
        return NewsSummariesBucket.SUMMARY_KEY.format(
            summaries_dir=NewsSummariesBucket.SUMMARIES_DIR,
            stock=stock.upper(),
            date=NewsSummariesBucket._get_datestamp(datestamp),
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
