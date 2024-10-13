import json
import os
from dataclasses import dataclass

from src.aws.sqs.client import WalterSQSClient
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class NewsletterRequest:
    email: str

    def to_message(self) -> dict:
        return self.__dict__()

    def __dict__(self) -> dict:
        return {"email": self.email}

    def __str__(self) -> str:
        return json.dumps(self.__dict__(), indent=4)


@dataclass
class NewslettersQueue:

    QUEUE_URL_FORMAT = (
        "https://sqs.{region}.amazonaws.com/{account_id}/NewslettersQueue-{domain}"
    )

    client: WalterSQSClient

    queue_url: str = None

    def __post_init__(self) -> None:
        self.queue_url = self._get_queue_url()
        log.debug(f"Creating NewslettersQueue with queue URL: '{self.queue_url}'")

    def add_newsletter_request(self, request: NewsletterRequest) -> str:
        log.info(f"Adding newsletter request to queue:\n{request}")
        message_id = self.client.send_message(
            queue_url=self.queue_url, message=request.to_message()
        )
        log.info(f"Added newsletter request to queue with message ID: {message_id}")
        return message_id

    def delete_newsletter_request(self, receipt_handle: str) -> None:
        log.info(
            f"Deleting newsletter request with the following receipt handle: {receipt_handle}"
        )
        self.client.delete_event(
            queue_url=self.queue_url, receipt_handle=receipt_handle
        )
        log.info("Successfully deleted newsletter request from queue")

    def _get_queue_url(self) -> str:
        return NewslettersQueue.QUEUE_URL_FORMAT.format(
            region=self.client.client.meta.region_name,
            account_id=os.getenv("AWS_ACCOUNT_ID"),
            domain=self.client.domain.value,
        )
