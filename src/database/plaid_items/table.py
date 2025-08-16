from dataclasses import dataclass
from typing import List, Optional

from src.aws.dynamodb.client import WalterDDBClient
from src.database.plaid_items.model import PlaidItem
from src.environment import Domain
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class PlaidItemsTable:
    """
    WalterDB: PlaidItemsTable
    """

    TABLE_NAME_FORMAT = "PlaidItems-{domain}"

    # Global Secondary Indexes (GSIs)
    USER_INSTITUTION_INDEX_NAME_FORMAT = "PlaidItems-UserInstitutionIndex-{domain}"
    ITEM_ID_INDEX_NAME_FORMAT = "PlaidItems-ItemIdIndex-{domain}"

    ddb: WalterDDBClient
    domain: Domain

    table_name: str = None  # set during post init
    item_id_index_name: str = None  # set during post init

    def __post_init__(self) -> None:
        self.table_name = PlaidItemsTable._get_table_name(self.domain)
        self.item_id_index_name = PlaidItemsTable._get_item_id_index_name(self.domain)
        log.debug(f"Initializing PlaidItemsTable with table name '{self.table_name}'")

    def get_item(self, user_id: str, item_id: str) -> Optional[PlaidItem]:
        """
        Retrieves a specific Plaid item for a user.

        Args:
            user_id: The user ID to retrieve the item for.
            item_id: The ID of the Plaid item.

        Returns:
            A `PlaidItem` object if found; otherwise, None.
        """
        log.info(f"Getting Plaid item '{item_id}' for user '{user_id}'")
        item = self.ddb.get_item(
            table=self.table_name,
            key=PlaidItemsTable._get_primary_key(user_id, item_id),
        )
        if not item:
            log.warning(f"Plaid item '{item_id}' for user '{user_id}' not found")
            return None
        return PlaidItem.get_item_from_ddb_item(item)

    def get_item_by_user_and_institution(
        self, user_id: str, institution_id: str
    ) -> Optional[PlaidItem]:
        log.info(
            f"Getting Plaid item from table '{self.table_name}' for user '{user_id}' with institution ID '{institution_id}'"
        )
        expression = "user_id = :user_id AND institution_id = :institution_id"
        attributes = {
            ":user_id": {"S": PlaidItem.get_user_id_key(user_id)},
            ":institution_id": {"S": institution_id},
        }
        item = self.ddb.query_index(
            self.table_name,
            self._get_user_institution_index_name(self.domain),
            expression,
            attributes,
        )
        return None if item is None else PlaidItem.get_item_from_ddb_item(item)

    def get_item_by_item_id(self, item_id: str) -> Optional[PlaidItem]:
        log.info(
            f"Getting Plaid item from table '{self.table_name}' with item ID: '{item_id}'"
        )
        expression = "item_id = :item_id"
        attributes = {":item_id": {"S": PlaidItem.get_item_id_key(item_id)}}
        item = self.ddb.query_index(
            self.table_name, self.item_id_index_name, expression, attributes
        )
        return None if item is None else PlaidItem.get_item_from_ddb_item(item)

    def get_items(self, user_id: str) -> List[PlaidItem]:
        """
        Retrieves all Plaid items for a given user.

        Args:
            user_id: The user ID to retrieve Plaid items for.

        Returns:
            A list of `PlaidItem` objects.
        """
        log.info(f"Getting all Plaid items for user from table '{self.table_name}'")

        items = self.ddb.query(
            table=self.table_name, query=PlaidItemsTable._get_items_by_user_key(user_id)
        )

        plaid_items = []
        for item in items:
            plaid_items.append(PlaidItem.get_item_from_ddb_item(item))

        log.info(f"Retrieved {len(plaid_items)} Plaid items for user!")

        return plaid_items

    def put_item(self, item: PlaidItem) -> PlaidItem:
        """
        Creates a new Plaid item.

        Args:
            item: The `PlaidItem` object to store in the database.

        Returns:
            The same `PlaidItem` object.
        """
        log.info(
            f"Putting Plaid item with item ID '{item.item_id}' to table '{self.table_name}'"
        )
        self.ddb.put_item(self.table_name, item.to_ddb_item())
        return item

    def delete_item(self, user_id: str, item_id: str) -> None:
        """
        Deletes a specific Plaid item for a user.

        Args:
            user_id: The user ID associated with the item.
            item_id: The ID of the Plaid item to delete.

        Returns:
            None.
        """
        log.info(f"Deleting Plaid item '{item_id}' for user '{user_id}'")
        self.ddb.delete_item(
            table=self.table_name,
            key=PlaidItemsTable._get_primary_key(user_id, item_id),
        )

    @staticmethod
    def _get_primary_key(user_id: str, item_id: str) -> dict:
        """
        Generates the primary key for the Plaid item.

        Args:
            user_id: The user ID to associate with the key.
            item_id: The ID of the Plaid item.

        Returns:
            A dictionary representing the primary key.
        """
        return {
            "user_id": {"S": PlaidItem.get_user_id_key(user_id)},
            "item_id": {"S": PlaidItem.get_item_id_key(item_id)},
        }

    @staticmethod
    def _get_items_by_user_key(user_id: str) -> dict:
        return {
            "user_id": {
                "AttributeValueList": [{"S": PlaidItem.get_user_id_key(user_id)}],
                "ComparisonOperator": "EQ",
            }
        }

    @staticmethod
    def _get_table_name(domain: Domain) -> str:
        """
        Generates the table name for the given domain.

        Args:
            domain: The domain to generate the table name for.

        Returns:
            The name of the DynamoDB table.
        """
        return PlaidItemsTable.TABLE_NAME_FORMAT.format(domain=domain.value)

    @staticmethod
    def _get_user_institution_index_name(domain: Domain) -> str:
        return PlaidItemsTable.USER_INSTITUTION_INDEX_NAME_FORMAT.format(
            domain=domain.value
        )

    @staticmethod
    def _get_item_id_index_name(domain: Domain) -> str:
        return PlaidItemsTable.ITEM_ID_INDEX_NAME_FORMAT.format(domain=domain.value)
