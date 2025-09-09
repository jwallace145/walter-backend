import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from src.aws.dynamodb.client import WalterDDBClient
from src.database.accounts.models import Account
from src.environment import Domain
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class AccountsTable:
    """Accounts Table"""

    TABLE_NAME_FORMAT = "Accounts-{domain}"

    ddb: WalterDDBClient
    domain: Domain

    table_name: str = None  # set during post-init

    def __post_init__(self) -> None:
        self.table_name = self.TABLE_NAME_FORMAT.format(domain=self.domain.value)
        log.debug(f"Initializing Accounts Table with name '{self.table_name}'")

    def create_account(
        self,
        user_id: str,
        account_type: str,
        account_subtype: str,
        institution_name: str,
        account_name: str,
        account_mask: str,
        balance: float,
        plaid_institution_id: Optional[str] = None,
        plaid_account_id: Optional[str] = None,
        plaid_access_token: Optional[str] = None,
        plaid_item_id: Optional[str] = None,
        plaid_last_sync_at: Optional[datetime] = None,
    ) -> Account:
        """
        Creates a new account for a specified user with provided details. Optionally integrates
        Plaid account information if related details are supplied. Logs the creation process
        and stores the account details in the database.

        Args:
            user_id (str): The identifier of the user owning the account.
            account_type (str): The type of the account (e.g., checking, savings).
            account_subtype (str): The subtype of the account (e.g., personal, business).
            institution_name (str): Name of the financial institution associated with the account.
            account_name (str): Custom name provided for the account.
            account_mask (str): Masked account number for security purposes.
            balance (float): Initial balance of the account.
            plaid_institution_id (Optional[str]): ID of the institution provided by Plaid, if available.
            plaid_account_id (Optional[str]): Plaid-specific account identifier, if available.
            plaid_access_token (Optional[str]): Access token for the Plaid account, if available.
            plaid_item_id (Optional[str]): Plaid item ID associated with the user's account, if available.
            plaid_last_sync_at (Optional[datetime]): Timestamp indicating the last sync time with Plaid,
                if applicable.

        Returns:
            Account: The newly created account object.
        """
        args = {
            "user_id": user_id,
            "account_type": account_type,
            "account_subtype": account_subtype,
            "institution_name": institution_name,
            "account_name": account_name,
            "account_mask": account_mask,
            "balance": balance,
        }
        log.info(f"Creating new {account_type.lower()} account for user '{user_id}'")

        # add optional plaid account institution/account/token args
        if plaid_institution_id:
            args["plaid_institution_id"] = plaid_institution_id
        if plaid_account_id:
            args["plaid_account_id"] = plaid_account_id
        if plaid_access_token:
            args["plaid_access_token"] = plaid_access_token
        if plaid_item_id:
            args["plaid_item_id"] = plaid_item_id
        if plaid_last_sync_at:
            args["plaid_last_sync_at"] = plaid_last_sync_at

        log.debug(f"Account args:\n{json.dumps(args, indent=4)}")

        account = Account.create(**args)
        self.ddb.put_item(self.table_name, account.to_ddb_item())

        log.info("Account created successfully!")

        return account

    def get_account(self, user_id: str, account_id: str) -> Optional[Account]:
        log.info(f"Getting '{account_id}' account for user '{user_id}'")
        account = self.ddb.get_item(
            self.table_name, AccountsTable._get_primary_key(user_id, account_id)
        )
        if account is None:
            log.info(f"Account '{account_id}' not found!")
            return None
        return Account.from_ddb_item(account)

    def get_account_by_plaid_account_id(
        self, plaid_account_id: str
    ) -> Optional[Account]:
        log.info(f"Getting account by Plaid account ID '{plaid_account_id}'")
        items = self.ddb.query(
            self.table_name,
            AccountsTable._get_account_by_plaid_account_id(plaid_account_id),
        )
        if not items:
            log.info(f"Account with Plaid account ID '{plaid_account_id}' not found!")
            return None
        if len(items) > 1:
            log.warning(
                f"Multiple accounts found with Plaid account ID '{plaid_account_id}'!"
            )
        return Account.from_ddb_item(items[0])

    def get_accounts(self, user_id: str) -> List[Account]:
        log.info(f"Getting all accounts for user '{user_id}'")
        accounts = self.ddb.query(
            self.table_name, AccountsTable._get_accounts_by_user_key(user_id)
        )
        log.info(f"Found {len(accounts)} account(s) for user!")
        return [Account.from_ddb_item(account) for account in accounts]

    def update_account(self, account: Account) -> Account:
        log.info(
            f"Updating account '{account.account_id}' for user '{account.user_id}'"
        )
        account.updated_at = datetime.now(timezone.utc)
        self.ddb.put_item(self.table_name, account.to_ddb_item())
        log.info(f"Account '{account.account_id}' put successfully!")
        return account

    def delete_account(self, user_id: str, account_id: str) -> None:
        log.info(f"Deleting account '{account_id}' for user '{user_id}'")
        self.ddb.delete_item(
            table=self.table_name,
            key=AccountsTable._get_primary_key(user_id, account_id),
        )
        log.info(f"Account '{account_id}' deleted successfully!")

    @staticmethod
    def _get_primary_key(user_id: str, account_id: str) -> dict:
        return {
            "user_id": {"S": user_id},
            "account_id": {"S": account_id},
        }

    @staticmethod
    def _get_accounts_by_user_key(user_id: str) -> dict:
        return {
            "user_id": {
                "AttributeValueList": [{"S": user_id}],
                "ComparisonOperator": "EQ",
            }
        }

    @staticmethod
    def _get_account_by_plaid_account_id(plaid_account_id: str) -> dict:
        return {
            "plaid_account_id": {
                "AttributeValueList": [{"S": plaid_account_id}],
                "ComparisonOperator": "EQ",
            }
        }
