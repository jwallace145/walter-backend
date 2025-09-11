import os
from dataclasses import dataclass

from src.aws.sqs.client import WalterSQSClient
from src.utils.log import Logger

LOG = Logger(__name__).get_logger()


@dataclass
class SyncUserTransactionsTask:
    """
    SyncUserTransactions Task
    """

    # SyncUserTransactions tasks are processed by the SyncUserTransactions workflow
    WORKFLOW_NAME = "SyncUserTransactions"

    user_id: str
    plaid_item_id: str

    def to_dict(self) -> dict:
        return {
            "workflow_name": self.WORKFLOW_NAME,
            "user_id": self.user_id,
            "plaid_item_id": self.plaid_item_id,
        }


@dataclass
class SyncUserTransactionsTaskQueue:
    """
    SyncUserTransactions Task Queue
    """

    # the queue name format must stay in sync with terraform to ensure proper queue url
    QUEUE_NAME_FORMAT = "WalterBackend-SyncTransactions-Queue-{domain}"
    QUEUE_URL_FORMAT = "https://sqs.{region}.amazonaws.com/{account_id}/{queue_name}"

    client: WalterSQSClient

    # the queue url is set during post-init
    queue_url: str = None

    def __post_init__(self) -> None:
        self.queue_url = SyncUserTransactionsTaskQueue.QUEUE_URL_FORMAT.format(
            region=self.client.client.meta.region_name,
            account_id=os.getenv("AWS_ACCOUNT_ID", "010526272437"),
            queue_name=SyncUserTransactionsTaskQueue.QUEUE_NAME_FORMAT.format(
                domain=self.client.domain.value
            ),
        )
        LOG.debug(
            f"Initializing SyncUserTransactionsQueue with queue URL: '{self.queue_url}'"
        )

    def add_task(self, task: SyncUserTransactionsTask) -> str:
        """
        Adds a SyncUserTransactions task to the queue.

        Args:
            task (SyncUserTransactionsTask): The task to be added to the queue.

        Returns:
            str: The ID of the added task message in the queue.
        """
        LOG.info("Adding SyncUserTransactions task to queue")
        LOG.debug(f"SyncUserTransactionsTask:\n{task}")
        message_id = self.client.send_message(
            queue_url=self.queue_url, message=task.to_dict()
        )
        LOG.info(f"Added SyncUserTransactions task to queue with ID: '{message_id}'")
        return message_id

    def delete_task(self, task_id: str) -> None:
        """
        Deletes a task from the queue using the specified task ID.

        Args:
            task_id: The unique identifier for the task to be deleted from the
                queue.
        """
        LOG.info(f"Deleting SyncUserTransactions task from queue with ID: {task_id}")
        self.client.delete_event(queue_url=self.queue_url, receipt_handle=task_id)
        LOG.info("Successfully deleted SyncUserTransactions task from queue")
