import datetime as dt

import pytest

from src.aws.s3.client import WalterS3Client
from src.environment import Domain
from src.news.bucket import NewsSummariesBucket
from src.stocks.alphavantage.models import CompanyNews
from src.summaries.models import NewsSummary

##########################
# NEWS SUMMARIES BUCKETS #
##########################

NEWS_SUMMARIES_BUCKET_TEST = "walterai-news-summaries-unittest"
NEWS_SUMMARIES_BUCKET_DEV = "walterai-news-summaries-dev"
NEWS_SUMMARIES_BUCKET_PREPROD = "walterai-news-summaries-preprod"
NEWS_SUMMARIES_BUCKET_PROD = "walterai-news-summaries-prod"

##################
# NEWS SUMMARIES #
##################

END_DATE = dt.datetime(
    year=2025, month=1, day=1, hour=0, minute=0, second=0, microsecond=0
)
START_DATE = END_DATE - dt.timedelta(days=90)
DATESTAMP = END_DATE

MSFT_SUMMARY_METADATA_KEY = "summaries/MSFT/y=2025/m=01/d=01/metadata.json"
MSFT_SUMMARY_KEY = "summaries/MSFT/y=2025/m=01/d=01/summary.html"

ABNB_SUMMARY_METADATA_KEY = "summaries/ABNB/y=2025/m=01/d=01/metadata.json"
ABNB_SUMMARY_KEY = "summaries/ABNB/y=2025/m=01/d=01/summary.html"
ABNB_SUMMARY = NewsSummary(
    stock="ABNB",
    company="airbnb",
    datestamp=DATESTAMP,
    model_name="unit-test",
    news=CompanyNews(
        stock="ABNB",
        company="airbnb",
        start_date=START_DATE,
        end_date=END_DATE,
        articles=[],
    ),
    summary="",
)

################################
# NEWS SUMMARIES BUCKET CLIENT #
################################


@pytest.fixture
def news_summaries_bucket(walter_s3: WalterS3Client) -> NewsSummariesBucket:
    return NewsSummariesBucket(walter_s3, Domain.TESTING)


##############
# UNIT TESTS #
##############


def test_put_summary(
    news_summaries_bucket: NewsSummariesBucket, walter_s3: WalterS3Client
) -> None:
    stock = "ABNB"
    assert (
        walter_s3.get_object(
            NEWS_SUMMARIES_BUCKET_TEST,
            f"summaries/{stock}/{DATESTAMP.strftime('y=%Y/m=%m/d=%d')}/metadata.json",
        )
        is None
    )
    assert (
        walter_s3.get_object(
            NEWS_SUMMARIES_BUCKET_TEST,
            f"summaries/{stock}/{DATESTAMP.strftime('y=%Y/m=%m/d=%d')}/summary.html",
        )
        is None
    )
    news_summaries_bucket.put_news_summary(ABNB_SUMMARY)
    assert (
        walter_s3.get_object(
            NEWS_SUMMARIES_BUCKET_TEST,
            f"summaries/{stock}/{DATESTAMP.strftime('y=%Y/m=%m/d=%d')}/metadata.json",
        )
        is not None
    )
    assert (
        walter_s3.get_object(
            NEWS_SUMMARIES_BUCKET_TEST,
            f"summaries/{stock}/{DATESTAMP.strftime('y=%Y/m=%m/d=%d')}/summary.html",
        )
        is not None
    )


def test_get_summary_does_exist(
    news_summaries_bucket: NewsSummariesBucket, walter_s3: WalterS3Client
) -> None:
    stock = "MSFT"
    now = dt.datetime.now()
    assert (
        walter_s3.get_object(
            NEWS_SUMMARIES_BUCKET_TEST,
            f"summaries/{stock}/{now.strftime('y=%Y/m=%m/d=%d')}/summary.html",
        )
        is not None
    )
    assert news_summaries_bucket.get_news_summary("MSFT") is not None


def test_get_summary_does_not_exist(
    news_summaries_bucket: NewsSummariesBucket, walter_s3: WalterS3Client
) -> None:
    stock = "ABNB"
    now = dt.datetime.now()
    assert (
        walter_s3.get_object(
            NEWS_SUMMARIES_BUCKET_TEST,
            f"summaries/{stock}/{now.strftime('y=%Y/m=%m/d=%d')}/summary.html",
        )
        is None
    )
    assert news_summaries_bucket.get_news_summary(stock) is None


def test_get_news_summaries_bucket_name() -> None:
    assert (
        NewsSummariesBucket._get_bucket_name(Domain.TESTING)
        == NEWS_SUMMARIES_BUCKET_TEST
    )
    assert (
        NewsSummariesBucket._get_bucket_name(Domain.DEVELOPMENT)
        == NEWS_SUMMARIES_BUCKET_DEV
    )
    assert (
        NewsSummariesBucket._get_bucket_name(Domain.STAGING)
        == NEWS_SUMMARIES_BUCKET_PREPROD
    )
    assert (
        NewsSummariesBucket._get_bucket_name(Domain.PRODUCTION)
        == NEWS_SUMMARIES_BUCKET_PROD
    )


def test_get_news_summary_metadata_key() -> None:
    datestamp = dt.datetime(year=2025, month=1, day=1)
    assert (
        NewsSummariesBucket._get_metadata_key("MSFT", datestamp)
        == MSFT_SUMMARY_METADATA_KEY
    )
    assert (
        NewsSummariesBucket._get_metadata_key("ABNB", datestamp)
        == ABNB_SUMMARY_METADATA_KEY
    )


def test_get_news_summary_key() -> None:
    datestamp = dt.datetime(year=2025, month=1, day=1)
    assert NewsSummariesBucket._get_summary_key("MSFT", datestamp) == MSFT_SUMMARY_KEY
    assert NewsSummariesBucket._get_summary_key("ABNB", datestamp) == ABNB_SUMMARY_KEY
