import json
from dataclasses import dataclass
from typing import List, Set, Tuple

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
        user_id, plaid_item_id = task_args

        # verify user and account exists with plaid credentials
        user: User = self._verify_user_exists(user_id)
        accounts: List[Account] = self._verify_accounts_exist(
            user.user_id, plaid_item_id
        )

        # get plaid access token for account(s)
        token: str = self._get_plaid_access_token(accounts)

        # sync transactions for account with plaid
        response: SyncTransactionsResponse = self.plaid.sync_transactions(
            user_id, token, cursor=None
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
            data={
                "user_id": user.user_id,
                "plaid_item_id": plaid_item_id,
                "accounts": [account.to_dict() for account in accounts],
            },
        )

    def _get_task_args(self, event: dict) -> Tuple[str, str]:
        LOG.info("Getting task args from event")
        LOG.debug(f"Event: {event}")
        try:
            # parse sqs message body to get user id and account id
            body = json.loads(event["Records"][0]["body"])
            user_id = body["user_id"]
            plaid_item_id = body["plaid_item_id"]
        except KeyError as e:
            raise ValueError(f"Missing required field: {e}")
        except Exception as e:
            raise ValueError(f"Invalid event: {e}")
        return user_id, plaid_item_id

    def _verify_user_exists(self, user_id: str) -> User:
        LOG.info(f"Verifying user '{user_id}' exists")
        user: User = self.db.get_user_by_id(user_id)
        if user is None:
            raise ValueError(f"User '{user_id}' does not exist!")
        LOG.info(f"Verified user '{user_id}' exists!")
        return user

    def _verify_accounts_exist(self, user_id: str, plaid_item_id: str) -> List[Account]:
        LOG.info(f"Verifying account(s) exist with Plaid item ID '{plaid_item_id}'")
        accounts: List[Account] = self.db.get_accounts_by_plaid_item_id(plaid_item_id)

        if len(accounts) == 0:
            LOG.error(f"Plaid item ID '{plaid_item_id}' does not include any accounts!")
            raise ValueError(
                f"Plaid item ID '{plaid_item_id}' does not include any accounts!"
            )

        LOG.info(
            f"Verified Plaid item ID '{plaid_item_id}' includes {len(accounts)} account(s)!"
        )

        for account in accounts:
            LOG.info(f"Verifying Plaid access token for account '{account.account_id}'")
            if account.plaid_access_token is None:
                raise ValueError(
                    f"Account '{account.account_id}' does not have a Plaid access token!"
                )

            LOG.info(f"Verified plaid access token for account '{account.account_id}'")

        return accounts

    def _get_plaid_access_token(self, accounts: List[Account]) -> str:
        LOG.info(f"Getting Plaid access token for {len(accounts)} account(s)")
        access_tokens: Set[str] = set(
            [account.plaid_access_token for account in accounts]
        )
        if len(access_tokens) == 0:
            raise ValueError("No Plaid access tokens found for account(s)")
        if len(access_tokens) > 1:
            raise ValueError("Multiple Plaid access tokens found for account(s)")
        LOG.info(f"Verified single Plaid access token for {len(accounts)} account(s)")
        return access_tokens[0]
