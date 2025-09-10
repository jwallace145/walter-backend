from dataclasses import dataclass
from typing import Tuple

from src.database.accounts.models import Account
from src.database.client import WalterDB
from src.database.users.models import User
from src.environment import Domain
from src.metrics.client import DatadogMetricsClient
from src.plaid.client import PlaidClient
from src.plaid.models import SyncTransactionsResponse
from src.utils.log import Logger
from src.workflows.common.models import Workflow, WorkflowResponse, WorkflowStatus

LOG = Logger(__name__).get_logger()


@dataclass
class SyncUserTransactions(Workflow):
    """
    Workflow for synchronizing user transactions with Plaid data.

    Processes task messages from a queue to sync transaction data for user accounts.
    Supports multiple trigger methods:
    - Scheduled synchronization via chronological jobs
    - Real-time updates via Plaid webhooks
    - On-demand refresh through API requests

    The workflow retrieves the latest transaction changes from Plaid and updates
    the local database accordingly, handling added, modified, and removed transactions.
    """

    WORKFLOW_NAME = "SyncUserTransactions"

    plaid: PlaidClient
    db: WalterDB

    def __init__(
        self,
        domain: Domain,
        plaid: PlaidClient,
        db: WalterDB,
        metrics: DatadogMetricsClient,
    ) -> None:
        super().__init__(SyncUserTransactions.WORKFLOW_NAME, domain, metrics)
        self.plaid = plaid
        self.db = db

    def execute(self, event: dict, emit_metrics: bool = True) -> WorkflowResponse:
        # get sync transaction task args from event
        task_args: Tuple[str, str] = self._get_task_args(event)
        user_id, account_id = task_args

        # verify user and account exists with plaid credentials
        user: User = self._verify_user_exists(user_id)
        account: Account = self._verify_account_exists(user_id, account_id)

        # sync transactions for account with plaid
        response: SyncTransactionsResponse = self.plaid.sync_transactions(
            user_id, account.plaid_access_token
        )

        # decompose plaid sync transactions response
        response.cursor  # TODO: What to do with this?
        response.synced_at  # TODO: What to do with this?
        added_transactions = response.added_transactions
        modified_transactions = response.modified_transactions
        removed_transactions = response.removed_transactions

        for transaction in added_transactions:
            self.db.add_transaction(transaction)

        for transaction in modified_transactions:
            self.db.edit_transaction(transaction)

        for transaction in removed_transactions:
            self.db.delete_transaction(
                transaction.account_id,
                transaction.transaction_id,
                transaction.transaction_date,
            )

        return WorkflowResponse(
            name=SyncUserTransactions.WORKFLOW_NAME,
            status=WorkflowStatus.SUCCESS,
            message="Successfully synced user transactions!",
            data={"user_id": user.user_id, "account": account.account_id},
        )

    def _get_task_args(self, event: dict) -> Tuple[str, str]:
        LOG.info("Getting task args from event")
        LOG.debug(f"Event: {event}")
        try:
            user_id = event["user_id"]
            account_id = event["account_id"]
        except KeyError as e:
            raise ValueError(f"Missing required field: {e}")
        except Exception as e:
            raise ValueError(f"Invalid event: {e}")
        return user_id, account_id

    def _verify_user_exists(self, user_id: str) -> User:
        LOG.info(f"Verifying user '{user_id}' exists")
        user: User = self.db.get_user_by_id(user_id)
        if user is None:
            raise ValueError(f"User '{user_id}' does not exist!")
        LOG.info(f"Verified user '{user_id}' exists!")
        return user

    def _verify_account_exists(self, user_id: str, account_id: str) -> Account:
        LOG.info(f"Verifying account '{account_id}' exists for user '{user_id}'")
        account: Account = self.db.get_account(user_id, account_id)
        if account is None:
            raise ValueError(f"Account '{account_id}' does not exist!")
        LOG.info(f"Verified account '{account_id}' exists for user '{user_id}'!")

        LOG.info(
            f"Verifying plaid access token and plaid item id for account '{account_id}'"
        )
        if account.plaid_access_token is None:
            raise ValueError(
                f"Account '{account_id}' does not have a Plaid access token!"
            )

        if account.plaid_item_id is None:
            raise ValueError(f"Account '{account_id}' does not have a Plaid item ID!")

        LOG.info(
            f"Verified plaid access token and plaid item id for account '{account_id}'"
        )

        return account
