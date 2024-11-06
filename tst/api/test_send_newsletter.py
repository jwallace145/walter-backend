import pytest
from mypy_boto3_sqs.client import SQSClient

from src.api.methods import Status, HTTPStatus
from src.api.send_newsletter import SendNewsletter
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.newsletters.queue import NewslettersQueue
from tst.api.utils import get_send_newsletter_event, get_expected_response


@pytest.fixture
def send_newsletter_api(
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
    newsletters_queue: NewslettersQueue,
    walter_sm: WalterSecretsManagerClient,
) -> SendNewsletter:
    return SendNewsletter(walter_cw, walter_db, newsletters_queue, walter_sm)


def test_send_newsletter(
    send_newsletter_api: SendNewsletter, sqs_client: SQSClient, jwt_walter: str
) -> None:
    event = get_send_newsletter_event(token=jwt_walter)
    expected_response = get_expected_response(
        api_name=send_newsletter_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.SUCCESS,
        message="Newsletter sent!",
    )
    sqs_client.receive_message(
        QueueUrl=send_newsletter_api.newsletters_queue.queue_url, MaxNumberOfMessages=1
    )
    assert expected_response == send_newsletter_api.invoke(event)
