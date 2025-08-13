import datetime as dt
from dataclasses import dataclass
from typing import List, Optional

from src.aws.dynamodb.client import WalterDDBClient
from src.database.transactions.models import (
    Transaction,
    TransactionType,
    InvestmentTransaction,
    BankTransaction,
)
from src.environment import Domain
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class TransactionsTable:
    """Transactions Table

    Responsible for creating, updating, getting, and deleting
    transactions in the DynamoDB Transactions table.
    """

    TABLE_NAME_FORMAT = "Transactions-{domain}"

    ddb: WalterDDBClient
    domain: Domain

    table_name: str = None  # set during post-init

    def __post_init__(self) -> None:
        self.table_name = self.TABLE_NAME_FORMAT.format(domain=self.domain.value)
        log.debug(f"Initializing Transactions Table with name '{self.table_name}'")

    def get_transaction(
        self, account_id: str, date: dt.datetime, transaction_id: str
    ) -> Optional[Transaction]:
        """Get a single transaction by account, date, and transaction id."""
        log.info(
            f"Getting transaction '{transaction_id}' for account '{account_id}' on date '{date.date()}'"
        )
        item = self.ddb.get_item(
            table=self.table_name,
            key=TransactionsTable._get_primary_key(account_id, date, transaction_id),
        )
        if item is None:
            log.info(
                f"Transaction '{transaction_id}' for account '{account_id}' on date '{date.date()}' not found!"
            )
            return None
        return TransactionsTable._from_ddb_item(item)

    def get_transactions(
        self, account_id: str, start_date: dt.datetime, end_date: dt.datetime
    ) -> List[Transaction]:
        """Get all transactions for an account between start_date and end_date (inclusive)."""
        log.info(
            f"Getting transactions for account '{account_id}' between '{start_date.date()}' and '{end_date.date()}'"
        )
        lower = TransactionsTable._sort_key_prefix(start_date) + "#"
        upper = TransactionsTable._sort_key_prefix(end_date) + "#~"
        items = self.ddb.query(
            table=self.table_name,
            query={
                "account_id": {
                    "AttributeValueList": [{"S": account_id}],
                    "ComparisonOperator": "EQ",
                },
                "transaction_date": {
                    "AttributeValueList": [{"S": lower}, {"S": upper}],
                    "ComparisonOperator": "BETWEEN",
                },
            },
        )
        transactions = [TransactionsTable._from_ddb_item(item) for item in items]
        log.info(f"Found {len(transactions)} transactions for account '{account_id}'")
        return transactions

    def get_transactions_by_account(self, account_id: str) -> List[Transaction]:
        """Get all transactions for a given account."""
        log.info(f"Getting all transactions for account '{account_id}'")
        return self.get_transactions(account_id, dt.datetime.min, dt.datetime.max)

    def put_transaction(self, transaction: Transaction) -> Transaction:
        """
        Add or update a transaction in the table.

        If callers change the transaction date, they should delete the old entry first
        to avoid duplicates, as the date is part of the sort key.
        """
        log.info(
            f"Putting transaction '{transaction.transaction_id}' for account '{transaction.account_id}'"
        )
        self.ddb.put_item(self.table_name, transaction.to_ddb_item())
        log.info("Transaction put successfully!")
        return transaction

    def delete_transaction(
        self, account_id: str, date: dt.datetime, transaction_id: str
    ) -> None:
        log.info(
            f"Deleting transaction '{transaction_id}' for account '{account_id}' on date '{date.date()}'"
        )
        self.ddb.delete_item(
            table=self.table_name,
            key=TransactionsTable._get_primary_key(account_id, date, transaction_id),
        )
        log.info("Transaction deleted successfully!")

    @staticmethod
    def _sort_key_prefix(date: dt.datetime) -> str:
        return date.strftime("%Y-%m-%d")

    @staticmethod
    def _get_primary_key(
        account_id: str, date: dt.datetime, transaction_id: str
    ) -> dict:
        return {
            "account_id": {"S": account_id},
            "transaction_date": {
                "S": f"{TransactionsTable._sort_key_prefix(date)}#{transaction_id}",
            },
        }

    @staticmethod
    def _from_ddb_item(item: dict) -> Transaction:
        """Deserialize a DDB item into the appropriate Transaction subclass."""
        txn_type_val = item["transaction_type"]["S"].lower()
        if txn_type_val == TransactionType.INVESTMENT.value:
            return InvestmentTransaction.from_ddb_item(item)
        else:
            return BankTransaction.from_ddb_item(item)
