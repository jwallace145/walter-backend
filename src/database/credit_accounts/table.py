from dataclasses import dataclass
from typing import List

from src.aws.dynamodb.client import WalterDDBClient
from src.database.credit_accounts.models import CreditAccount
from src.environment import Domain
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class CreditAccountsTable:
    """
    WalterDB: CreditAccountsTable
    """

    TABLE_NAME_FORMAT = "CreditAccounts-{domain}"

    ddb: WalterDDBClient
    domain: Domain

    table_name: str = None  # set during post-init

    def __post_init__(self) -> None:
        self.table_name = CreditAccountsTable._get_table_name(self.domain)
        print(f"Initializing CreditAccountsTable with table name '{self.table_name}'")

    def create_account(self, account: CreditAccount) -> CreditAccount:
        log.info(f"Creating a new credit account:\n{account.to_dict()}")
        self.ddb.put_item(self.table_name, account.to_ddb_item())
        return account

    def get_accounts(self, user_id: str) -> List[CreditAccount]:
        log.info(f"Getting credit accounts for user from table '{self.table_name}'")

        credit_account_items = self.ddb.query(
            table=self.table_name,
            query=CreditAccountsTable._get_accounts_by_user_key(user_id),
        )

        credit_accounts = []
        for item in credit_account_items:
            credit_accounts.append(CreditAccount.get_account_from_ddb_item(item))

        log.info(f"Returned {len(credit_accounts)} credit accounts for user!")

        return credit_accounts

    @staticmethod
    def _get_accounts_by_user_key(user_id: str) -> dict:
        return {
            "user_id": {
                "AttributeValueList": [{"S": CreditAccount.get_user_id_key(user_id)}],
                "ComparisonOperator": "EQ",
            }
        }

    @staticmethod
    def _get_table_name(domain: Domain) -> str:
        return CreditAccountsTable.TABLE_NAME_FORMAT.format(domain=domain.value)
