import json

import pytest

from src.api.common.models import HTTPStatus, Status
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.events.parser import WalterEventParser
from src.news.bucket import NewsSummariesBucket
from src.news.queue import NewsSummariesQueue
from src.stocks.alphavantage.models import CompanyNews, NewsArticle
from src.summaries.client import WalterNewsSummaryClient
from src.summaries.models import NewsSummary
from src.workflows.create_news_summary_and_archive import CreateNewsSummaryAndArchive
import datetime as dt

from tst.events.utils import get_create_news_summary_and_archive_event

#############
# CONSTANTS #
#############

MODEL_NAME = "Amazon: Nova Micro"
MSFT_STOCK = "MSFT"
DATE = dt.datetime(year=2025, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
MSFT_NEWS_SUMMARY = NewsSummary(
    stock=MSFT_STOCK,
    datestamp=DATE,
    model_name=MODEL_NAME,
    news=CompanyNews(
        stock=MSFT_STOCK,
        start_date=DATE - dt.timedelta(days=365),
        end_date=DATE,
        articles=[
            NewsArticle(
                title="test-title",
                url="test-url",
                published_timestamp=DATE,
                authors=["walter"],
                source="test-source",
                summary="test-summary",
                contents="test-contents",
            )
        ],
    ),
    summary="test-summary",
)

############
# FIXTURES #
############


class MockWalterNewsSummaryClient:
    def generate(
        self,
        stock: str,
        start_date: dt.datetime,
        end_date: dt.datetime,
        number_of_articles: int,
    ) -> NewsSummary | None:
        if stock.upper() == MSFT_STOCK:
            return MSFT_NEWS_SUMMARY
        raise ValueError(
            f"MockWalterNewsSummaryClient does not implement generate news summary for stock '{stock.upper()}'!"
        )


@pytest.fixture
def walter_news_summary_client() -> MockWalterNewsSummaryClient:
    return MockWalterNewsSummaryClient()


@pytest.fixture
def create_news_summary_and_archive_workflow(
    walter_event_parser: WalterEventParser,
    walter_news_summary_client: WalterNewsSummaryClient,
    news_summaries_bucket: NewsSummariesBucket,
    news_summaries_queue: NewsSummariesQueue,
    walter_cw: WalterCloudWatchClient,
) -> CreateNewsSummaryAndArchive:
    return CreateNewsSummaryAndArchive(
        walter_event_parser,
        walter_news_summary_client,
        news_summaries_bucket,
        news_summaries_queue,
        walter_cw,
    )


#########
# TESTS #
#########


def test_create_news_summary_and_archive_success(
    create_news_summary_and_archive_workflow: CreateNewsSummaryAndArchive,
) -> None:
    event = get_create_news_summary_and_archive_event(
        MSFT_STOCK, DATE.strftime("%Y-%m-%d")
    )
    response = create_news_summary_and_archive_workflow.invoke(event)
    assert response == {
        "statusCode": HTTPStatus.CREATED.value,
        "body": json.dumps(
            {
                "Workflow": "CreateNewsSummaryAndArchive",
                "Status": Status.SUCCESS.value,
                "Message": "News summary created!",
                "Data": {
                    "s3_uri": "s3://walterai-news-summaries-unittest/summaries/MSFT/y=2025/m=01/d=01/summary.html",
                    "summary": {
                        "model_name": MODEL_NAME,
                        "stock": MSFT_STOCK,
                        "datestamp": DATE.strftime("%Y-%m-%d"),
                        "summary": "test-summary",
                    },
                },
            }
        ),
    }
