import json

import pytest
from mypy_boto3_sqs.client import SQSClient

from src.api.models import Status, HTTPStatus
from src.api.send_newsletter import SendNewsletter
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.newsletters.queue import NewslettersQueue
from tst.api.utils import get_send_newsletter_event


@pytest.fixture
def send_newsletter_api(
    walter_db: WalterDB,
    newsletters_queue: NewslettersQueue,
    walter_sm: WalterSecretsManagerClient,
) -> SendNewsletter:
    return SendNewsletter(walter_db, newsletters_queue, walter_sm)


def test_send_newsletter(
    send_newsletter_api: SendNewsletter, sqs_client: SQSClient, jwt_walter: str
) -> None:
    event = get_send_newsletter_event(email="walter@gmail.com", token=jwt_walter)
    expected_response = get_expected_response(
        status_code=HTTPStatus.OK, status=Status.SUCCESS, message="Newsletter sent!"
    )
    sqs_client.receive_message(
        QueueUrl=send_newsletter_api.newsletters_queue.queue_url, MaxNumberOfMessages=1
    )
    assert expected_response == send_newsletter_api.invoke(event)


def test_send_newsletter_failure_invalid_email(
    send_newsletter_api: SendNewsletter, sqs_client: SQSClient, jwt_walter: str
) -> None:
    event = get_send_newsletter_event(email="walter", token=jwt_walter)
    expected_response = get_expected_response(
        status_code=HTTPStatus.OK, status=Status.FAILURE, message="Invalid email!"
    )
    assert expected_response == send_newsletter_api.invoke(event)


def get_expected_response(
    status_code: HTTPStatus, status: Status, message: str
) -> dict:
    return {
        "statusCode": status_code.value,
        "body": json.dumps(
            {
                "API": "WalterAPI: SendNewsletter",
                "Status": status.value,
                "Message": message,
            }
        ),
    }
