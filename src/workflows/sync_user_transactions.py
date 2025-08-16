import json
from dataclasses import dataclass

from src.api.common.models import HTTPStatus, Status
from src.database.client import WalterDB
from src.events.parser import WalterEventParser
from src.plaid.client import PlaidClient
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class SyncUserTransactions:

    WORKFLOW_NAME = "SyncUserTransactions"

    parser: WalterEventParser
    plaid: PlaidClient
    db: WalterDB

    def invoke(self, event: dict) -> dict:
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
        # removed_transactions = response.removed_transactions

        for transaction in added_transactions:
            self.db.put_transaction(transaction)

        for transaction in modified_transactions:
            self.db.put_transaction(transaction)

        # TODO: Implement syncing the removed transactions as well

        plaid_item.cursor = cursor
        plaid_item.synced_at = synced_at
        self.db.put_plaid_item(plaid_item)

        return {
            "statusCode": HTTPStatus.OK.value,
            "body": json.dumps(
                {
                    "Workflow": SyncUserTransactions.WORKFLOW_NAME,
                    "Status": Status.SUCCESS.value,
                    "Message": "Successfully synced user transactions!",
                    "Data": {
                        "user_id": user_id,
                        "plaid_item_id": plaid_item.item_id,
                        "cursor": plaid_item.cursor,
                        "synced_at": plaid_item.synced_at.isoformat(),
                    },
                }
            ),
        }
