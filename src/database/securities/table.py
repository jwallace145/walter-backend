from dataclasses import dataclass
from typing import List, Optional, Union

from src.aws.dynamodb.client import WalterDDBClient
from src.database.securities.models import Crypto, Security, SecurityType, Stock
from src.environment import Domain
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class SecuritiesTable:
    """Securities Table

    Responsible for creating, updating, getting, listing, and deleting
    securities in the DynamoDB Securities table.
    """

    TABLE_NAME_FORMAT = "Securities-{domain}"

    ddb: WalterDDBClient
    domain: Domain

    table_name: str = None  # set during post-init

    def __post_init__(self) -> None:
        self.table_name = self.TABLE_NAME_FORMAT.format(domain=self.domain.value)
        log.debug(f"Initializing Securities Table with name '{self.table_name}'")

    def create_security(self, security: Security) -> Security:
        security_type = security.security_type.value
        log.info(f"Creating new {security_type} security")
        self.ddb.put_item(self.table_name, security.to_ddb_item())
        log.info(f"{security_type} security created successfully!")
        return security

    def get_security(self, security_id: str) -> Optional[Security]:
        log.info(f"Getting security '{security_id}' from table '{self.table_name}'")
        item = self.ddb.get_item(
            table=self.table_name,
            key=SecuritiesTable._get_primary_key(security_id),
        )
        if item is None:
            log.info(f"Security '{security_id}' not found!")
            return None
        return SecuritiesTable._from_ddb_item(item)

    def get_security_by_ticker(self, ticker: str) -> Optional[Security]:
        log.info(
            f"Getting security by ticker '{ticker}' from table '{self.table_name}'"
        )
        items = self.ddb.query_index(
            table=self.table_name,
            index_name=f"Securities-TickerIndex-{self.domain.value}",
            expression="ticker = :ticker",
            attributes={":ticker": {"S": ticker}},
        )
        if not items:
            log.info(f"Security with ticker '{ticker}' not found!")
            return None
        return SecuritiesTable._from_ddb_item(items[0])

    def get_securities(self) -> List[Security]:
        log.info(f"Getting all securities from table '{self.table_name}'")
        securities = []
        for item in self.ddb.scan_table(self.table_name):
            securities.append(SecuritiesTable._from_ddb_item(item))
        return securities

    def update_security(self, security: Security) -> Security:
        log.info(f"Updating security '{security.security_id}'")
        self.ddb.put_item(self.table_name, security.to_ddb_item())
        log.info(f"Security '{security.security_id}' updated successfully!")
        return security

    def delete_security(self, security_id: str) -> None:
        log.info(f"Deleting security '{security_id}' from table '{self.table_name}'")
        self.ddb.delete_item(
            table=self.table_name, key=SecuritiesTable._get_primary_key(security_id)
        )
        log.info(f"Security '{security_id}' deleted successfully!")

    @staticmethod
    def _get_primary_key(security_id: str) -> dict:
        return {
            "security_id": {"S": security_id},
        }

    @staticmethod
    def _from_ddb_item(item: dict) -> Union[Stock, Crypto]:
        security_type = SecurityType.from_string(item["security_type"]["S"])
        match security_type:
            case SecurityType.STOCK:
                return Stock.from_ddb_item(item)
            case SecurityType.CRYPTO:
                return Crypto.from_ddb_item(item)
            case _:
                raise ValueError(f"Invalid security type '{security_type}'!")
