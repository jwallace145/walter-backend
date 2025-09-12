import json
from dataclasses import dataclass
from typing import Tuple

from src.api.common.exceptions import (
    AccountDoesNotExist,
    BadRequest,
    NotAuthenticated,
    PlaidAccessTokenDoesNotExist,
    PlaidItemDoesNotExist,
    UserDoesNotExist,
)
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Response, Status
from src.auth.authenticator import WalterAuthenticator
from src.database.accounts.models import Account
from src.database.client import WalterDB
from src.database.users.models import User
from src.environment import Domain
from src.metrics.client import DatadogMetricsClient
from src.transactions.queue import (
    SyncUserTransactionsTask,
    SyncUserTransactionsTaskQueue,
)
from src.utils.log import Logger

LOG = Logger(__name__).get_logger()


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
    REQUIRED_FIELDS = ["user_id", "account_id"]
    EXCEPTIONS = [
        (NotAuthenticated, HTTPStatus.UNAUTHORIZED),
        (AccountDoesNotExist, HTTPStatus.NOT_FOUND),
        (PlaidAccessTokenDoesNotExist, HTTPStatus.NOT_FOUND),
        (PlaidItemDoesNotExist, HTTPStatus.NOT_FOUND),
        (UserDoesNotExist, HTTPStatus.NOT_FOUND),
        (BadRequest, HTTPStatus.BAD_REQUEST),
    ]

    queue: SyncUserTransactionsTaskQueue

    def __init__(
        self,
        domain: Domain,
        walter_authenticator: WalterAuthenticator,
        metrics: DatadogMetricsClient,
        db: WalterDB,
        queue: SyncUserTransactionsTaskQueue,
    ) -> None:
        super().__init__(
            domain,
            SyncTransactions.API_NAME,
            SyncTransactions.REQUIRED_QUERY_FIELDS,
            SyncTransactions.REQUIRED_HEADERS,
            SyncTransactions.REQUIRED_FIELDS,
            SyncTransactions.EXCEPTIONS,
            walter_authenticator,
            metrics,
            db,
        )
        self.queue = queue

    def execute(self, event: dict, authenticated_email: str) -> Response:
        args: Tuple[str, str] = self._get_request_args(event)
        user_id, account_id = args
        user: User = self._verify_user_exists(user_id)
        account: Account = self._verify_account_exists(user_id, account_id)
        self._add_task_to_queue(user_id, account.plaid_item_id)
        return Response(
            domain=self.domain,
            api_name=SyncTransactions.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Added task to queue!",
            data={
                "user_id": user.user_id,
                "account_id": account.account_id,
                "institution_name": account.institution_name,
                "account_name": account.account_name,
            },
        )

    def _get_request_args(self, event: dict) -> Tuple[str, str]:
        """
        Extracts 'user_id' and 'account_id' from the body of an event payload. Logs
        the process and raises specific errors when the necessary fields are missing
        or invalid.

        Args:
            event (dict): The event dictionary containing the 'body' key from which
                the 'user_id' and 'account_id' are extracted.

        Raises:
            BadRequest: If 'user_id' or 'account_id' is missing from the request body.
            BadRequest: If the 'user_id' or 'account_id' in the request body is invalid.

        Returns:
            Tuple[str, str]: A tuple containing the 'user_id' and 'account_id', both
            represented as strings.
        """
        LOG.info("Getting 'user_id' and 'account_id' from request body")
        try:
            body = json.loads(event["body"])
            user_id = body["user_id"]
            account_id = body["account_id"]
            return user_id, account_id
        except KeyError:
            raise BadRequest("Missing 'user_id' or 'account_id' in request body!")
        except Exception:
            raise BadRequest("Invalid 'user_id' or 'account_id' in request body!")

    def _verify_account_exists(self, user_id: str, account_id: str) -> Account:
        """
        Verifies that an account exists for a given user ID and account ID.

        This method retrieves an account from the database for the given user ID and
        account ID. It ensures that the account exists and has valid Plaid credentials,
        including a Plaid access token and a Plaid item ID. If the account does not
        exist or its Plaid credentials are missing, exceptions are raised.

        Args:
            user_id: The ID of the user associated with the account.
            account_id: The ID of the account to verify.

        Returns:
            The retrieved account if it exists and has valid Plaid credentials.

        Raises:
            AccountDoesNotExist: If the account with the specified ID does not exist.
            PlaidAccessTokenDoesNotExist: If the account does not have a Plaid
                access token.
            PlaidItemDoesNotExist: If the account does not have a Plaid item ID.
        """
        LOG.info(f"Getting account '{account_id}' for user '{user_id}'")
        account = self.db.get_account(user_id, account_id)
        if account is None:
            raise AccountDoesNotExist(f"Account '{account_id}' does not exist!")
        LOG.info(f"Account '{account_id}' successfully retrieved from database!")

        LOG.info(
            f"Verifying plaid access token and plaid item id for account '{account_id}'"
        )
        if account.plaid_access_token is None:
            LOG.error(f"Account '{account_id}' does not have a Plaid access token!")
            raise PlaidAccessTokenDoesNotExist(
                f"Account '{account_id}' does not have a Plaid access token!"
            )

        if account.plaid_item_id is None:
            LOG.error(f"Account '{account_id}' does not have a Plaid item ID!")
            raise PlaidItemDoesNotExist(
                f"Account '{account_id}' does not have a Plaid item ID!"
            )

        return account

    def _add_task_to_queue(self, user_id: str, account: Account) -> None:
        """
        Adds a synchronize user transactions task to the queue for processing.

        Args:
            user_id: The unique identifier of the user for whom the task is being added.
            account: The account object that contains the Plaid item ID.
        """
        LOG.info(
            f"Adding sync transactions task to queue for account '{account.account_id}' and Plaid item ID '{account.plaid_item_id}'"
        )
        task = SyncUserTransactionsTask(user_id, account.plaid_item_id)
        self.queue.add_task(task)
        LOG.info("Sync user transactions event successfully added to queue!")

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return False
