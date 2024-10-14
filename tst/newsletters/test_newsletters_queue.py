import json

import pytest
from mypy_boto3_sqs import SQSClient

from src.aws.sqs.client import WalterSQSClient
from src.database.users.models import User
from src.environment import Domain
from src.newsletters.queue import NewslettersQueue, NewsletterRequest

WALTER = User(
    email="walter@gmail.com", username="walter", password_hash="password", salt="salt"
)

ADD_NEWSLETTER_REQUEST = NewsletterRequest(
    email=WALTER.email,
)

NEWSLETTER_QUEUE_URL = (
    "https://sqs.us-east-1.amazonaws.com/012345678901/NewslettersQueue-unittest"
)


@pytest.fixture
def newsletters_queue(sqs_client: SQSClient) -> NewslettersQueue:
    return NewslettersQueue(
        client=WalterSQSClient(client=sqs_client, domain=Domain.TESTING)
    )


def test_get_queue_url(newsletters_queue: NewslettersQueue) -> None:
    assert NEWSLETTER_QUEUE_URL == newsletters_queue._get_queue_url()


def test_add_newsletter_request(
    newsletters_queue: NewslettersQueue, sqs_client: SQSClient
) -> None:
    message_id = newsletters_queue.add_newsletter_request(ADD_NEWSLETTER_REQUEST)
    messages = sqs_client.receive_message(QueueUrl=NEWSLETTER_QUEUE_URL)
    assert message_id is not None
    assert (
        json.loads(messages["Messages"][0]["Body"])
        == ADD_NEWSLETTER_REQUEST.to_message()
    )


def test_delete_newsletter_request(
    newsletters_queue: NewslettersQueue, sqs_client: SQSClient
) -> None:
    message_id = newsletters_queue.add_newsletter_request(ADD_NEWSLETTER_REQUEST)
    receipt_handle = sqs_client.receive_message(QueueUrl=NEWSLETTER_QUEUE_URL)[
        "Messages"
    ][0]["ReceiptHandle"]
    newsletters_queue.delete_newsletter_request(receipt_handle)
    messages = sqs_client.receive_message(QueueUrl=NEWSLETTER_QUEUE_URL)
    assert message_id is not None
    assert "Messages" not in messages
