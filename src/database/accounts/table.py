import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, List

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
    ) -> Account:
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
        log.debug(f"Account args:\n{json.dumps(args, indent=4)}")
        account = Account.create_new_account(
            user_id=user_id,
            account_type=account_type,
            account_subtype=account_subtype,
            institution_name=institution_name,
            account_name=account_name,
            account_mask=account_mask,
            balance=balance,
        )
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

    def get_accounts(self, user_id: str) -> List[Account]:
        log.info(f"Getting all accounts for user '{user_id}'")
        accounts = self.ddb.query(
            self.table_name, AccountsTable._get_accounts_by_user_key(user_id)
        )
        log.info(f"Found {len(accounts)} accounts for user!")
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
