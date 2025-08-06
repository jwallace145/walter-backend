from dataclasses import dataclass
from typing import List, Optional

from src.aws.dynamodb.client import WalterDDBClient
from src.database.accounts.cash.models import CashAccount
from src.environment import Domain
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class CashAccountsTable:
    """
    WalterDB: CashAccountsTable
    """

    TABLE_NAME_FORMAT = "CashAccounts-{domain}"

    ddb: WalterDDBClient
    domain: Domain

    table_name: str = None  # set during post init

    def __post_init__(self) -> None:
        self.table_name = CashAccountsTable._get_table_name(self.domain)
        log.debug(f"Initializing CashAccountsTable with table name '{self.table_name}'")

    def get_account(self, user_id: str, account_id: str) -> Optional[CashAccount]:
        log.info(f"Getting cash account '{account_id}' for user '{user_id}'")
        account_item = self.ddb.get_item(
            table=self.table_name,
            key=CashAccountsTable._get_primary_key(user_id, account_id),
        )
        if not account_item:
            return None
        return CashAccount.get_account_from_ddb_item(account_item)

    def get_accounts(self, user_id: str) -> List[CashAccount]:
        """
        Retrieves all cash accounts for the given user.

        Args:
            user_id: The user ID to retrieve accounts for.

        Returns:
            A list of `CashAccount` objects.
        """
        log.info(f"Getting cash accounts for user from table '{self.table_name}'")

        cash_account_items = self.ddb.query(
            table=self.table_name,
            query=CashAccountsTable._get_accounts_by_user_key(user_id),
        )

        cash_accounts = []
        for item in cash_account_items:
            cash_accounts.append(CashAccount.get_account_from_ddb_item(item))

        log.info(f"Returned {len(cash_accounts)} cash accounts for user!")

        return cash_accounts

    def create_account(self, account: CashAccount) -> CashAccount:
        """
        Creates a new cash account.

        Args:
            account: The `CashAccount` object to create.

        Returns:
            None.
        """
        log.info(f"Creating a new account: {account.to_dict()}")
        self.ddb.put_item(self.table_name, account.to_ddb_item())
        return account

    def update_account(self, account: CashAccount) -> None:
        """
        Updates the balance of an existing cash account.

        Args:
            account: The `CashAccount` object to update.

        Returns:
            None.
        """
        log.info(f"Updating user account '{account.bank_name} {account.account_name}'")
        self.ddb.put_item(self.table_name, account.to_ddb_item())

    def delete_account(self, user_id: str, account_id: str) -> None:
        """
        Deletes a cash account.

        Args:
            user_id: The ID of the user who owns the account.
            account_id: The ID of the account to delete.

        Returns:
            None.
        """
        self.ddb.delete_item(
            table=self.table_name,
            key=CashAccountsTable._get_primary_key(user_id, account_id),
        )

    @staticmethod
    def _get_primary_key(user_id: str, account_id: str) -> dict:
        return {
            "user_id": {"S": CashAccount.get_user_id_key(user_id)},
            "account_id": {"S": CashAccount.get_account_id_key(account_id)},
        }

    @staticmethod
    def _get_accounts_by_user_key(user_id: str) -> dict:
        return {
            "user_id": {
                "AttributeValueList": [{"S": CashAccount.get_user_id_key(user_id)}],
                "ComparisonOperator": "EQ",
            }
        }

    @staticmethod
    def _get_table_name(domain: Domain) -> str:
        return CashAccountsTable.TABLE_NAME_FORMAT.format(domain=domain.value)
