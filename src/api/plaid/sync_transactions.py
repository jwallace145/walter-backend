import json
from dataclasses import dataclass

from src.api.common.exceptions import (
    BadRequest,
    NotAuthenticated,
    PlaidItemDoesNotExist,
    UserDoesNotExist,
)
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Response, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.database.plaid_items.model import PlaidItem
from src.database.users.models import User
from src.transactions.queue import (
    SyncUserTransactionsQueue,
    SyncUserTransactionsSQSEvent,
)
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class SyncTransactions(WalterAPIMethod):
    """
    WalterAPI: SyncTransactions

    This API endpoint handles transaction synchronization between Plaid and WalterDB.
    It serves two main purposes:

    1. Acts as a Plaid webhook endpoint that receives notifications when new transactions
       are available for a user. Upon receipt, it queues a sync request to fetch and
       store the latest transactions asynchronously.

    2. Supports manual sync requests that can be triggered outside Plaid webhooks.
       These requests are created by a scheduled job to ensure that user transactions
       are periodically synchronized regardless of the Plaid webhooks.
    """

    API_NAME = "SyncTransactions"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {}
    REQUIRED_FIELDS = ["item_id", "webhook_code"]
    EXCEPTIONS = [NotAuthenticated, PlaidItemDoesNotExist, UserDoesNotExist, BadRequest]

    db: WalterDB
    queue: SyncUserTransactionsQueue

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        db: WalterDB,
        queue: SyncUserTransactionsQueue,
    ) -> None:
        super().__init__(
            SyncTransactions.API_NAME,
            SyncTransactions.REQUIRED_QUERY_FIELDS,
            SyncTransactions.REQUIRED_HEADERS,
            SyncTransactions.REQUIRED_FIELDS,
            SyncTransactions.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.db = db
        self.queue = queue

    def execute(self, event: dict, authenticated_email: str) -> Response:
        item_id = self._get_item_id(event)
        webhook_code = self._get_webhook_code(event)
        log.info(f"webhook code: {webhook_code}")
        item = self._get_plaid_item(item_id)
        self._add_sync_transactions_request_to_queue(
            user_id=item.get_user_id(), plaid_item_id=item.get_item_id()
        )
        return Response(
            api_name=SyncTransactions.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Syncing user transactions!",
            data={
                "user_id": item.get_user_id(),
                "institution_id": item.institution_id,
                "institution_name": item.institution_name,
            },
        )

    def _add_sync_transactions_request_to_queue(
        self, user_id: str, plaid_item_id: str
    ) -> None:
        """
        Handles the request to sync user transactions.

        Args:
            access_token (str): The access token associated with the user.
            webhook_code (str): The webhook event code from Plaid.

        Returns:
            dict: Response object indicating success or error details.
        """
        log.info(
            f"Adding request to sync user transactions for user '{user_id}' to queue..."
        )
        self.queue.add_sync_user_transactions_event(
            SyncUserTransactionsSQSEvent(user_id=user_id, plaid_item_id=plaid_item_id)
        )
        log.info("Sync user transactions event successfully added to queue!")

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return False

    def _verify_user_exists(self, email: str) -> User:
        log.info(f"Verifying user exists with email '{email}'")
        user = self.db.get_user_by_email(email)
        if user is None:
            raise UserDoesNotExist(f"User with email '{email}' does not exist!")
        log.info("Verified user exists!")
        return user

    def _get_item_id(self, event: dict) -> str:
        body = json.loads(event["body"])
        return body["item_id"]

    def _get_webhook_code(self, event: dict) -> str:
        body = json.loads(event["body"])
        return body["webhook_code"]

    def _get_plaid_item(self, item_id: str) -> PlaidItem:
        log.info("Getting Plaid item from WalterDB")
        plaid_item = self.db.get_plaid_item_by_item_id(item_id)
        if plaid_item is None:
            raise PlaidItemDoesNotExist("Plaid item does not exist!")
        log.info(
            f"Plaid item with item ID '{plaid_item.item_id}' successfully retrieved from WalterDB!"
        )
        return plaid_item
