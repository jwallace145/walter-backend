from dataclasses import dataclass
from typing import Optional, Union

from src.aws.dynamodb.client import WalterDDBClient
from src.database.securities.models import Security, SecurityType, Stock, Crypto
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
