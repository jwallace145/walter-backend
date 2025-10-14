import datetime as dt
from dataclasses import dataclass
from typing import List, Optional

from src.aws.dynamodb.client import WalterDDBClient
from src.database.transactions.models import (
    BankTransaction,
    InvestmentTransaction,
    Transaction,
    TransactionType,
)
from src.environment import Domain
from src.utils.log import Logger

LOG = Logger(__name__).get_logger()


@dataclass
class TransactionsTable:
    """Transactions Table

    Responsible for creating, updating, getting, and deleting
    transactions in the DynamoDB Transactions table.
    """

    TABLE_NAME_FORMAT = "Transactions-{domain}"

    # Global Secondary Indexes (GSIs)
    USER_DATE_RANGE_INDEX_NAME_FORMAT = "Transactions-UserDateRangeIndex-{domain}"
    ACCOUNT_DATE_RANGE_INDEX_NAME_FORMAT = "Transactions-AccountDateRangeIndex-{domain}"

    ddb: WalterDDBClient
    domain: Domain

    table_name: str = None  # set during post-init

    def __post_init__(self) -> None:
        self.table_name = self.TABLE_NAME_FORMAT.format(domain=self.domain.value)
        LOG.debug(f"Initializing Transactions Table with name '{self.table_name}'")

    def get_user_transaction(
        self,
        user_id: str,
        transaction_id: str,
    ) -> Optional[Transaction]:
        """Get a single transaction for a given user."""
        LOG.info(f"Getting transaction '{transaction_id}' for user '{user_id}'")
        item = self.ddb.get_item(
            table=self.table_name,
            key=TransactionsTable._get_primary_key(user_id, transaction_id),
        )
        if item is None:
            LOG.warning(
                f"Transaction '{transaction_id}' for user '{user_id}' not found!"
            )
            return None
        return TransactionsTable._from_ddb_item(item)

    def get_user_transactions(
        self, user_id: str, start_date: dt.datetime, end_date: dt.datetime
    ) -> List[Transaction]:
        """Get all transactions for a given user."""
        LOG.info(
            f"Getting transactions for user '{user_id}' between '{start_date.date()}' and '{end_date.date()}'"
        )
        lower = TransactionsTable._sort_key_prefix(start_date) + "#"
        upper = TransactionsTable._sort_key_prefix(end_date) + "#~"
        items = self.ddb.query_index(
            table=self.table_name,
            index_name=self._get_user_date_range_index_name(self.domain),
            expression="user_id = :user_id AND transaction_date BETWEEN :start_date AND :end_date",
            attributes={
                ":user_id": {"S": user_id},
                ":start_date": {"S": lower},
                ":end_date": {"S": upper},
            },
        )
        transactions = [TransactionsTable._from_ddb_item(item) for item in items]
        LOG.info(f"Found {len(transactions)} transactions for user '{user_id}'")
        return transactions

    def get_account_transactions(
        self,
        account_id: str,
        start_date: dt.datetime = dt.datetime.min,
        end_date: dt.datetime = dt.datetime.max,
    ) -> List[Transaction]:
        """Get all transactions for an account between start_date and end_date (inclusive)."""
        LOG.info(
            f"Getting transactions for account '{account_id}' between '{start_date.date()}' and '{end_date.date()}'"
        )
        lower = TransactionsTable._sort_key_prefix(start_date) + "#"
        upper = TransactionsTable._sort_key_prefix(end_date) + "#~"
        items = self.ddb.query_index(
            table=self.table_name,
            index_name=self._get_account_date_range_index(self.domain),
            expression="account_id = :account_id AND transaction_date BETWEEN :start_date AND :end_date",
            attributes={
                ":account_id": {"S": account_id},
                ":start_date": {"S": lower},
                ":end_date": {"S": upper},
            },
        )
        transactions = [TransactionsTable._from_ddb_item(item) for item in items]
        LOG.info(f"Found {len(transactions)} transactions for account '{account_id}'")
        return transactions

    def get_transactions_by_account(self, account_id: str) -> List[Transaction]:
        """Get all transactions for a given account."""
        LOG.info(f"Getting all transactions for account '{account_id}'")
        return self.get_account_transactions(
            account_id, dt.datetime.min, dt.datetime.max
        )

    def get_all_transactions(self) -> List[Transaction]:
        """Get all transactions."""
        LOG.info("Getting all transactions")
        items = self.ddb.scan_table(table=self.table_name)
        return [TransactionsTable._from_ddb_item(item) for item in items]

    def put_transaction(self, transaction: Transaction) -> Transaction:
        """
        Add or update a transaction in the table.

        If callers change the transaction date, they should delete the old entry first
        to avoid duplicates, as the date is part of the sort key.
        """
        LOG.info(
            f"Putting transaction '{transaction.transaction_id}' for account '{transaction.account_id}'"
        )
        self.ddb.put_item(self.table_name, transaction.to_ddb_item())
        LOG.info("Transaction put successfully!")
        return transaction

    def delete_transaction(self, user_id: str, transaction_id: str) -> None:
        LOG.info(f"Deleting transaction '{transaction_id}' for user '{user_id}'")
        self.ddb.delete_item(
            table=self.table_name,
            key=TransactionsTable._get_primary_key(user_id, transaction_id),
        )
        LOG.info("Transaction deleted successfully!")

    @staticmethod
    def _sort_key_prefix(date: dt.datetime) -> str:
        return date.strftime("%Y-%m-%d")

    @staticmethod
    def _get_primary_key(user_id: str, transaction_id: str) -> dict:
        return {
            "user_id": {"S": user_id},
            "transaction_id": {
                "S": transaction_id,
            },
        }

    @staticmethod
    def _get_user_date_range_index_name(domain: Domain) -> str:
        return TransactionsTable.USER_DATE_RANGE_INDEX_NAME_FORMAT.format(
            domain=domain.value
        )

    @staticmethod
    def _get_account_date_range_index(domain: Domain) -> str:
        return TransactionsTable.ACCOUNT_DATE_RANGE_INDEX_NAME_FORMAT.format(
            domain=domain.value
        )

    @staticmethod
    def _from_ddb_item(item: dict) -> Transaction:
        """Deserialize a DDB item into the appropriate Transaction subclass."""
        txn_type_val = item["transaction_type"]["S"].lower()
        if txn_type_val == TransactionType.INVESTMENT.value:
            return InvestmentTransaction.from_ddb_item(item)
        else:
            return BankTransaction.from_ddb_item(item)
