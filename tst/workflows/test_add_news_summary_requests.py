import json

import pytest

from src.api.common.models import HTTPStatus, Status
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.news.queue import NewsSummariesQueue
from src.workflows.add_news_summary_requests import AddNewsSummaryRequests

TEST_EVENT = {}
"""(dict): Test event to trigger AddNewsSummaryRequests workflow (event is empty because job is simply triggered by cron schedule)."""


@pytest.fixture
def add_news_summary_requests_workflow(
    walter_db: WalterDB,
    news_summaries_queue: NewsSummariesQueue,
    walter_cw: WalterCloudWatchClient,
) -> AddNewsSummaryRequests:
    return AddNewsSummaryRequests(walter_db, news_summaries_queue, walter_cw)


def test_add_news_summary_requests_success(
    add_news_summary_requests_workflow: AddNewsSummaryRequests,
) -> None:
    response = add_news_summary_requests_workflow.invoke(TEST_EVENT)
    assert response == {
        "statusCode": HTTPStatus.OK.value,
        "body": json.dumps(
            {
                "Workflow": "AddNewsSummaryRequests",
                "Status": Status.SUCCESS.value,
                "Message": "Added news summary requests!",
                "Data": {
                    "news_summary_queue": "https://sqs.us-east-1.amazonaws.com/012345678901/NewsSummariesQueue-unittest",
                    "number_of_stocks": 11,
                },
            }
        ),
    }
