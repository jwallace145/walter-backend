import json
from datetime import timedelta

import pytest

from src.api.common.models import HTTPStatus, Status
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.database.stocks.models import Stock
from src.events.parser import WalterEventParser
from src.news.bucket import NewsSummariesBucket
from src.news.queue import NewsSummariesQueue
from src.stocks.alphavantage.models import CompanyNews, NewsArticle
from src.stocks.client import WalterStocksAPI
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
MSFT_COMPANY = "Microsoft"
DATE = dt.datetime(year=2025, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
MSFT_NEWS_SUMMARY = NewsSummary(
    stock=MSFT_STOCK,
    company=MSFT_COMPANY,
    datestamp=DATE,
    model_name=MODEL_NAME,
    news=CompanyNews(
        stock=MSFT_STOCK,
        company=MSFT_COMPANY,
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
MSFT_NEWS_SUMMARY_2 = NewsSummary(
    stock=MSFT_STOCK,
    company=MSFT_COMPANY,
    datestamp=DATE + timedelta(days=1),
    model_name=MODEL_NAME,
    news=CompanyNews(
        stock=MSFT_STOCK,
        company=MSFT_COMPANY,
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
        stock: Stock,
        start_date: dt.datetime,
        end_date: dt.datetime,
        number_of_articles: int,
        context: str,
        prompt: str,
        max_length: int,
    ) -> NewsSummary | None:
        if stock.symbol.upper() == MSFT_STOCK and end_date == DATE:
            return MSFT_NEWS_SUMMARY
        elif stock.symbol.upper() == MSFT_STOCK and end_date == (
            DATE + timedelta(days=1)
        ):
            return MSFT_NEWS_SUMMARY_2
        raise ValueError(
            f"MockWalterNewsSummaryClient does not implement generate news summary for stock '{stock.symbol.upper()}' and date '{end_date}'!"
        )


@pytest.fixture
def walter_news_summary_client() -> MockWalterNewsSummaryClient:
    return MockWalterNewsSummaryClient()


@pytest.fixture
def create_news_summary_and_archive_workflow(
    walter_event_parser: WalterEventParser,
    walter_db: WalterDB,
    walter_stocks_api: WalterStocksAPI,
    walter_news_summary_client: WalterNewsSummaryClient,
    news_summaries_bucket: NewsSummariesBucket,
    news_summaries_queue: NewsSummariesQueue,
    walter_cw: WalterCloudWatchClient,
) -> CreateNewsSummaryAndArchive:
    return CreateNewsSummaryAndArchive(
        walter_event_parser,
        walter_db,
        walter_stocks_api,
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
    date = DATE + timedelta(days=1)
    event = get_create_news_summary_and_archive_event(
        MSFT_STOCK, date.strftime("%Y-%m-%d")
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
                    "s3_uri": "s3://walterai-news-summaries-unittest/summaries/MSFT/y=2025/m=01/d=02/summary.html",
                    "summary": {
                        "model_name": MODEL_NAME,
                        "stock": MSFT_STOCK,
                        "company": MSFT_COMPANY,
                        "datestamp": date.strftime("%Y-%m-%d"),
                        "summary": "test-summary",
                    },
                },
            }
        ),
    }
