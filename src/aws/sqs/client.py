import json
from dataclasses import dataclass

from botocore.exceptions import ClientError
from mypy_boto3_sqs.client import SQSClient

from src.environment import Domain
from src.utils.log import Logger

log = Logger(__name__).get_logger()

ACCOUNT_ID = "010526272437"


@dataclass
class WalterSQSClient:

    QUEUE_URL_FORMAT = (
        "https://sqs.{region}.amazonaws.com/{account_id}/NewslettersQueue-{domain}"
    )

    client: SQSClient
    domain: Domain

    queue_url: str = None

    def __post_init__(self) -> None:
        self.queue_url = self._get_queue_url()
        log.debug(
            f"Creating Walter SQS client in region '{self.client.meta.region_name}' with queue URL '{self.queue_url}'"
        )

    def publish_message(self, message: dict) -> None:
        log.debug(f"Publishing message to queue '{self.queue_url}'")
        try:
            self.client.send_message(QueueUrl=self.queue_url, MessageBody=json.dumps(message))
        except ClientError as error:
            log.error(
                f"Unexpected error occurred publishing message to queue '{self.queue_url}'\n"
                f"Error: {error.response['Error']['Message']}"
            )
            raise error

    def delete_event(self, receipt_handle: str) -> None:
        log.debug(
            f"Deleting message with the following receipt handle from queue '{self.queue_url}': {receipt_handle}"
        )
        try:
            self.client.delete_message(QueueUrl=self.queue_url, ReceiptHandle=receipt_handle)
        except ClientError as error:
            log.error(
                f"Unexpected error occurred deleting message from queue '{self.queue_url}'\n"
                f"Error: {error.response['Error']['Message']}"
            )
            raise error

    def _get_queue_url(self) -> str:
        return WalterSQSClient.QUEUE_URL_FORMAT.format(
            region=self.client.meta.region_name,
            account_id=ACCOUNT_ID,
            domain=self.domain.value,
        )
