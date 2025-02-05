import datetime as dt
import json
import os
from dataclasses import dataclass

from src.aws.sqs.client import WalterSQSClient
from src.utils.log import Logger

log = Logger(__name__).get_logger()

##########
# MODELS #
##########


@dataclass
class NewsSummaryRequest:
    datestamp: dt.datetime
    stock: str

    def __post_init__(self) -> None:
        self._verify_datestamp()

    def to_message(self) -> dict:
        return self.__dict__()

    def _verify_datestamp(self) -> None:
        truncated_datestamp = self.datestamp.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        if self.datestamp != truncated_datestamp:
            raise ValueError(
                f"Cannot create NewsSummaryRequest! Datestamp not truncated to a date: '{truncated_datestamp}'"
            )

    def __dict__(self) -> dict:
        return {
            "datestamp": self.datestamp.strftime("%Y-%m-%d"),
            "stock": self.stock,
        }

    def __str__(self) -> str:
        return json.dumps(self.__dict__(), indent=4)


##########
# CLIENT #
##########


@dataclass
class NewsSummariesQueue:
    """
    NewsSummariesQueue
    """

    QUEUE_URL_FORMAT = (
        "https://sqs.{region}.amazonaws.com/{account_id}/NewsSummariesQueue-{domain}"
    )

    client: WalterSQSClient

    queue_url: str = None  # set during post init

    def __post_init__(self) -> None:
        self.queue_url = self._get_queue_url()
        log.debug(f"Creating NewsSummaryQueue with queue URL: '{self.queue_url}'")

    def add_news_summary_request(self, request: NewsSummaryRequest) -> str:
        log.info(f"Adding news summary request to queue:\n{request}")
        message_id = self.client.send_message(
            queue_url=self.queue_url, message=request.to_message()
        )
        log.info(f"Added news summary request to queue with message ID: {message_id}")
        return message_id

    def delete_news_summary_request(self, receipt_handle: str) -> None:
        log.info(
            f"Deleting news summary request with the following receipt handle: {receipt_handle}"
        )
        self.client.delete_event(
            queue_url=self.queue_url, receipt_handle=receipt_handle
        )
        log.info("Successfully deleted news summary request from queue")

    def _get_queue_url(self) -> str:
        return NewsSummariesQueue.QUEUE_URL_FORMAT.format(
            region=self.client.client.meta.region_name,
            account_id=os.getenv(
                "AWS_ACCOUNT_ID", "010526272437"
            ),  # TODO: Fix me! AWS account IDs aren't meant to be private but get rid of it
            domain=self.client.domain.value,
        )
