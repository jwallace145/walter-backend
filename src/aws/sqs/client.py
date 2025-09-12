import json
from dataclasses import dataclass

from botocore.exceptions import ClientError
from mypy_boto3_sqs.client import SQSClient

from src.environment import Domain
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass(kw_only=True)
class WalterSQSClient:

    client: SQSClient
    domain: Domain

    def __post_init__(self) -> None:
        log.debug(
            f"Creating Walter SQS client in region '{self.client.meta.region_name}'"
        )

    def send_message(self, queue_url: str, message: dict) -> str:
        log.debug(f"Sending message to queue '{queue_url}'")
        try:
            return self.client.send_message(
                QueueUrl=queue_url, MessageBody=json.dumps(message)
            )["MessageId"]
        except ClientError as error:
            log.error(
                f"Unexpected error occurred publishing message to queue '{queue_url}'\n"
                f"Error: {error.response['Error']['Message']}"
            )
            raise error

    def delete_event(self, queue_url: str, receipt_handle: str) -> None:
        log.debug(
            f"Deleting message with the following receipt handle from queue '{queue_url}': {receipt_handle}"
        )
        try:
            self.client.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
        except ClientError as error:
            log.error(
                f"Unexpected error occurred deleting message from queue '{queue_url}'\n"
                f"Error: {error.response['Error']['Message']}"
            )
            raise error
