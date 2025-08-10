from dataclasses import dataclass
from typing import List, Optional

from src.aws.dynamodb.client import WalterDDBClient
from src.database.accounts.credit.models import CreditAccount
from src.database.accounts.investment.models import InvestmentAccount
from src.database.accounts.models import Account
from src.environment import Domain
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class InvestmentAccountsTable:
    """
    WalterDB: InvestmentAccountsTable
    """

    TABLE_NAME_FORMAT = "InvestmentAccounts-{domain}"

    ddb: WalterDDBClient
    domain: Domain

    table_name: str = None  # set during post-init

    def __post_init__(self) -> None:
        self.table_name = InvestmentAccountsTable._get_table_name(self.domain)
        log.debug(
            f"Initializing InvestmentAccounts table with table name '{self.table_name}'"
        )

    def create_account(self, account: InvestmentAccount) -> InvestmentAccount:
        log.info(f"Creating a new investment account:\n{account.to_dict()}")
        self.ddb.put_item(self.table_name, account.to_ddb_item())
        return account

    def get_account(self, user_id: str, account_id: str) -> Optional[InvestmentAccount]:
        log.info(f"Getting investment account '{account_id}' for user '{user_id}'")
        account_item = self.ddb.get_item(
            table=self.table_name,
            key=InvestmentAccountsTable._get_primary_key(user_id, account_id),
        )
        if not account_item:
            return None
        return CreditAccount.get_account_from_ddb_item(account_item)

    def get_accounts(self, user_id: str) -> List[InvestmentAccount]:
        log.info(f"Getting investment accounts for user from table '{self.table_name}'")

        investment_account_items = self.ddb.query(
            table=self.table_name,
            query=InvestmentAccountsTable._get_accounts_by_user_key(user_id),
        )

        investment_accounts = []
        for item in investment_account_items:
            investment_accounts.append(
                InvestmentAccount.get_account_from_ddb_item(item)
            )

        log.info(f"Returned {len(investment_accounts)} credit accounts for user!")

        return investment_accounts

    def delete_account(self, user_id: str, account_id: str) -> None:
        log.info(f"Deleting investment account '{account_id}' for user '{user_id}'")
        self.ddb.delete_item(
            table=self.table_name,
            key=InvestmentAccountsTable._get_primary_key(user_id, account_id),
        )

    @staticmethod
    def _get_primary_key(user_id: str, account_id: str) -> dict:
        return {
            "user_id": {"S": Account.get_user_id_key(user_id)},
            "account_id": {"S": Account.get_account_id_key(account_id)},
        }

    @staticmethod
    def _get_accounts_by_user_key(user_id: str) -> dict:
        return {
            "user_id": {
                "AttributeValueList": [{"S": Account.get_user_id_key(user_id)}],
                "ComparisonOperator": "EQ",
            }
        }

    @staticmethod
    def _get_table_name(domain: Domain) -> str:
        return InvestmentAccountsTable.TABLE_NAME_FORMAT.format(domain=domain.value)
