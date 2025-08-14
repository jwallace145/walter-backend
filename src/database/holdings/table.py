from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from src.aws.dynamodb.client import WalterDDBClient
from src.database.holdings.models import Holding
from src.environment import Domain
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class HoldingsTable:
    """Holdings Table

    Responsible for creating, updating, getting, and deleting
    holdings in the DynamoDB Holdings table.
    """

    TABLE_NAME_FORMAT = "Holdings-{domain}"

    ddb: WalterDDBClient
    domain: Domain

    table_name: str = None  # set during post-init

    def __post_init__(self) -> None:
        self.table_name = self.TABLE_NAME_FORMAT.format(domain=self.domain.value)
        log.debug(f"Initializing Holdings Table with name '{self.table_name}'")

    def create_holding(self, holding: Holding) -> Holding:
        log.info(
            f"Creating holding for account '{holding.account_id}' and security '{holding.security_id}'"
        )
        self.ddb.put_item(self.table_name, holding.to_ddb_item())
        log.info("Holding created successfully!")
        return holding

    def get_holding(self, account_id: str, security_id: str) -> Optional[Holding]:
        log.info(
            f"Getting holding for account '{account_id}' and security '{security_id}' from table '{self.table_name}'"
        )
        item = self.ddb.get_item(
            table=self.table_name,
            key=HoldingsTable._get_primary_key(account_id, security_id),
        )
        if item is None:
            log.info(
                f"Holding for account '{account_id}' and security '{security_id}' not found!"
            )
            return None
        return Holding.from_ddb_item(item)

    def get_holdings(self, account_id: str) -> List[Holding]:
        log.info(
            f"Getting all holdings for account '{account_id}' from table '{self.table_name}'"
        )
        items = self.ddb.query(
            table=self.table_name,
            query=HoldingsTable._get_holdings_by_account_key(account_id),
        )
        holdings = [Holding.from_ddb_item(item) for item in items]
        log.info(f"Found {len(holdings)} holding(s) for account '{account_id}'")
        return holdings

    def update_holding(self, holding: Holding) -> Holding:
        log.info(
            f"Updating holding for account '{holding.account_id}' and security '{holding.security_id}'"
        )
        holding.updated_at = datetime.now(timezone.utc)
        self.ddb.put_item(self.table_name, holding.to_ddb_item())
        log.info(
            f"Holding for account '{holding.account_id}' and security '{holding.security_id}' updated successfully!"
        )
        return holding

    def delete_holding(self, account_id: str, security_id: str) -> None:
        log.info(
            f"Deleting holding for account '{account_id}' and security '{security_id}' from table '{self.table_name}'"
        )
        self.ddb.delete_item(
            table=self.table_name,
            key=HoldingsTable._get_primary_key(account_id, security_id),
        )
        log.info(
            f"Holding for account '{account_id}' and security '{security_id}' deleted successfully!"
        )

    @staticmethod
    def _get_primary_key(account_id: str, security_id: str) -> dict:
        return {
            "account_id": {"S": account_id},
            "security_id": {"S": security_id},
        }

    @staticmethod
    def _get_holdings_by_account_key(account_id: str) -> dict:
        return {
            "account_id": {
                "AttributeValueList": [{"S": account_id}],
                "ComparisonOperator": "EQ",
            }
        }
