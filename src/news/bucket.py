import json
import re
from dataclasses import dataclass
from datetime import datetime as dt, datetime

from src.aws.s3.client import WalterS3Client
from src.database.stocks.models import Stock
from src.environment import Domain
from src.stocks.alphavantage.models import CompanyNews, NewsArticle
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
    METADATA_FILENAME = "metadata.json"
    SUMMARY_FILENAME = "summary.html"
    SUMMARIES_PREFIX = "{summaries_dir}/{stock}"
    METADATA_KEY = "{summaries_dir}/{stock}/{date}/{metadata_filename}"
    SUMMARY_KEY = "{summaries_dir}/{stock}/{date}/{summary_filename}"

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

    def get_news_summary(self, stock: Stock, date: dt = TODAY) -> NewsSummary | None:
        log.info(
            f"Getting news summary from archive for stock '{stock.symbol}' with date: '{date.strftime('%Y-%m-%d')}'..."
        )

        # attempt to get news summary metadata and return none if not found
        metadata_key = NewsSummariesBucket._get_metadata_key(stock.symbol, date)
        metadata = self.client.get_object(self.bucket, metadata_key)
        if metadata is None:
            return None

        metadata = NewsSummariesBucket._get_metadata(metadata)

        # attempt to get news summary and return none if not found as both metadata and summary are required
        summary_key = NewsSummariesBucket._get_summary_key(stock.symbol, date)
        summary = self.client.get_object(self.bucket, summary_key)
        if summary is None:
            return None

        # convert metadata and summary to proper NewsSummary object
        return NewsSummariesBucket._get_news_summary(metadata, summary)

    def get_latest_news_summary(self, stock: str) -> NewsSummary | None:
        log.info(f"Getting latest news summary for stock '{stock}'")

        prefix = NewsSummariesBucket._get_summaries_prefix(stock)
        objects = self.client.list_objects(self.bucket, prefix)

        # ensure summaries exist for given stock
        if len(objects) == 0:
            log.info("No summaries found for stock '{stock}'!")
            return None

        # filter keys by metadata and summary
        metadata_keys = [
            key for key in objects if NewsSummariesBucket.METADATA_FILENAME in key
        ]
        summary_keys = [
            key for key in objects if NewsSummariesBucket.SUMMARY_FILENAME in key
        ]

        # get latest metadata and summary objects
        metadata = json.loads(self.client.get_object(self.bucket, metadata_keys[-1]))
        summary = self.client.get_object(self.bucket, summary_keys[-1])

        return NewsSummary(
            stock=metadata["stock"],
            company=metadata["company"],
            datestamp=dt.strptime(metadata["datestamp"], "%Y-%m-%d"),
            model_name=metadata["model_name"],
            news=None,  # TODO: Eventually populate this field? Not need for this method yet as its only used by newsletter generation which doesn't care about the input news articles
            summary=self.remove_non_alphanumeric(
                summary
            ),  # This is necessary because the summary is markdown formatted and can cause YAML issues if markdown format specifiers are not removed
        )

    @staticmethod
    def _get_bucket_name(domain: Domain) -> str:
        return NewsSummariesBucket.BUCKET.format(domain=domain.value)

    @staticmethod
    def _get_metadata_key(stock: str, datestamp: dt):
        return NewsSummariesBucket.METADATA_KEY.format(
            summaries_dir=NewsSummariesBucket.SUMMARIES_DIR,
            stock=stock.upper(),
            date=NewsSummariesBucket._get_datestamp(datestamp),
            metadata_filename=NewsSummariesBucket.METADATA_FILENAME,
        )

    @staticmethod
    def _get_summary_key(stock: str, datestamp: dt) -> str:
        return NewsSummariesBucket.SUMMARY_KEY.format(
            summaries_dir=NewsSummariesBucket.SUMMARIES_DIR,
            stock=stock.upper(),
            date=NewsSummariesBucket._get_datestamp(datestamp),
            summary_filename=NewsSummariesBucket.SUMMARY_FILENAME,
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

    @staticmethod
    def _get_metadata(metadata: str) -> dict:
        return json.loads(metadata)

    @staticmethod
    def _get_news_summary(metadata: dict, summary: str) -> NewsSummary:
        return NewsSummary(
            stock=metadata["stock"],
            company=metadata["company"],
            datestamp=datetime.strptime(metadata["datestamp"], "%Y-%m-%d"),
            model_name=metadata["model_name"],
            news=NewsSummariesBucket._get_company_news(metadata),
            summary=summary,
        )

    @staticmethod
    def _get_company_news(metadata: dict) -> CompanyNews:
        print(metadata)
        return CompanyNews(
            stock=metadata["stock"],
            company=metadata["company"],
            start_date=datetime.strptime(metadata["news"]["start_date"], "%Y-%m-%d"),
            end_date=datetime.strptime(metadata["news"]["end_date"], "%Y-%m-%d"),
            articles=[
                NewsSummariesBucket._get_article(article)
                for article in metadata["news"]["articles"]
            ],
        )

    @staticmethod
    def _get_article(article: dict) -> NewsArticle:
        return NewsArticle(
            title=article["title"],
            url=article["url"],
            published_timestamp=datetime.strptime(
                article["published_timestamp"], "%Y-%m-%d"
            ),
            authors=article["authors"],
            source=article["source"],
            summary=article["summary"],
            contents=article["contents"],
        )

    def remove_non_alphanumeric(self, text: str) -> str:
        return re.sub(r"[^a-zA-Z0-9 ]", "", text)
