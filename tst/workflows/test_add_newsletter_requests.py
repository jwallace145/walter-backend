import json

import pytest

from src.api.common.models import HTTPStatus, Status
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.newsletters.queue import NewslettersQueue
from src.workflows.add_newsletter_requests import AddNewsletterRequests

TEST_EVENT = {}
"""(dict): Test event to trigger AddNewsletterRequests workflow (event is empty because job is simply triggered by cron schedule)."""


@pytest.fixture
def add_newsletter_requests_workflow(
    walter_db: WalterDB,
    newsletters_queue: NewslettersQueue,
    walter_cw: WalterCloudWatchClient,
) -> AddNewsletterRequests:
    return AddNewsletterRequests(walter_db, newsletters_queue, walter_cw)


def test_add_newsletter_requests_success(
    add_newsletter_requests_workflow: AddNewsletterRequests,
) -> None:
    response = add_newsletter_requests_workflow.invoke(TEST_EVENT)
    assert response == {
        "statusCode": HTTPStatus.OK.value,
        "body": json.dumps(
            {
                "Workflow": AddNewsletterRequests.WORKFLOW_NAME,
                "Status": Status.SUCCESS.value,
                "Message": "Added newsletter requests!",
                "Data": {
                    "newsletters_queue": "https://sqs.us-east-1.amazonaws.com/012345678901/NewslettersQueue-unittest",
                    "total_number_of_users_count": 8,
                    "verified_users_count": 7,
                    "unverified_users_count": 1,
                    "subscribed_users_count": 8,
                    "unsubscribed_users_count": 0,
                    "paid_users_count": 4,
                    "free_trial_users_count": 1,
                    "expired_free_trial_users_count": 3,
                    "total_number_of_newsletter_sent": 5,
                },
            }
        ),
    }
