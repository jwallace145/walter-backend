from dataclasses import dataclass

from src.database.client import WalterDB
from src.plaid.client import PlaidClient
from src.utils.log import Logger
from src.workflows.common.models import Workflow, WorkflowResponse, WorkflowStatus

log = Logger(__name__).get_logger()


@dataclass
class SyncUserTransactions(Workflow):

    WORKFLOW_NAME = "SyncUserTransactions"

    plaid: PlaidClient
    db: WalterDB

    def execute(self, event: dict) -> WorkflowResponse:
        event = self.parser.parse_sync_user_transactions_event(event)

        # decompose event
        user_id = event.user_id
        plaid_item_id = event.plaid_item_id

        plaid_item = self.db.plaid_items_table.get_item(user_id, plaid_item_id)
        if not plaid_item:
            raise ValueError("Plaid item does not exist!")

        response = self.plaid.sync_transactions(
            plaid_item.get_user_id(), plaid_item.access_token, plaid_item.cursor
        )

        # decompose plaid sync transactions response
        cursor = response.cursor
        synced_at = response.synced_at
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

        # TODO: Implement syncing the removed transactions as well

        plaid_item.cursor = cursor
        plaid_item.synced_at = synced_at
        self.db.put_plaid_item(plaid_item)

        return WorkflowResponse(
            name=SyncUserTransactions.WORKFLOW_NAME,
            status=WorkflowStatus.SUCCESS,
            message="Successfully synced user transactions!",
            data={
                "user_id": user_id,
                "plaid_item_id": plaid_item.item_id,
                "cursor": plaid_item.cursor,
                "synced_at": plaid_item.synced_at.isoformat(),
            },
        )
