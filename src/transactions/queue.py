import json
import os
from dataclasses import dataclass

from src.aws.sqs.client import WalterSQSClient
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class SyncUserTransactionsSQSEvent:
    user_id: str
    plaid_item_id: str

    def to_message(self) -> dict:
        return self.__dict__()

    def __dict__(self) -> dict:
        return {
            "user_id": self.user_id,
            "plaid_item_id": self.plaid_item_id,
        }

    def __str__(self) -> str:
        return json.dumps(self.__dict__(), indent=4)


@dataclass
class SyncUserTransactionsQueue:

    QUEUE_URL_FORMAT = "https://sqs.{region}.amazonaws.com/{account_id}/WalterBackend-SyncTransactions-Queue-{domain}"

    client: WalterSQSClient
    queue_url: str = None

    def __post_init__(self) -> None:
        self.queue_url = self._build_queue_url()
        log.debug(
            f"Initializing SyncUserTransactionsQueue with queue URL: '{self.queue_url}'"
        )

    def add_sync_user_transactions_event(
        self, event: SyncUserTransactionsSQSEvent
    ) -> str:
        """
        Adds a sync user transactions event to the queue.

        Args:
            event: The sync transactions event to add.

        Returns:
            The message ID of the added event.
        """
        log.info("Adding sync user transactions event to queue")
        log.debug(f"SyncUserTransactionsEvent:\n{event}")
        message_id = self.client.send_message(
            queue_url=self.queue_url, message=event.to_message()
        )
        log.info(
            f"Added sync user transactions event to queue with message ID: '{message_id}'"
        )
        return message_id

    def delete_sync_user_transactions_event(self, receipt_handle: str) -> None:
        """
        Deletes a sync user transactions event from the queue.

        Args:
            receipt_handle: The receipt handle of the event to delete.

        Returns:
            None.
        """
        log.info(
            f"Deleting sync user transactions event with receipt handle: {receipt_handle}"
        )
        self.client.delete_event(
            queue_url=self.queue_url, receipt_handle=receipt_handle
        )
        log.info("Successfully deleted sync user transactions event from queue")

    def _build_queue_url(self) -> str:
        """
        Constructs and returns the queue URL based on the domain.

        Returns:
            The queue URL.
        """
        return SyncUserTransactionsQueue.QUEUE_URL_FORMAT.format(
            region=self.client.client.meta.region_name,
            account_id=os.getenv("AWS_ACCOUNT_ID", "010526272437"),
            domain=self.client.domain.value,
        )
