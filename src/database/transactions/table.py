import datetime as dt
import json
from dataclasses import dataclass
from typing import List, Optional

from src.aws.dynamodb.client import WalterDDBClient
from src.database.transactions.models import Transaction
from src.environment import Domain
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class TransactionsTable:

    TABLE_NAME_FORMAT = "Transactions-{domain}"

    ddb: WalterDDBClient
    domain: Domain

    table: str = None  # set during post init

    def __post_init__(self) -> None:
        self.table = TransactionsTable._get_table_name(self.domain)
        log.debug(
            f"Creating Transactions table DynamoDB client with table name '{self.table}'"
        )

    def get_transaction(
        self, user_id: str, date: dt.datetime, transaction_id: str
    ) -> Optional[Transaction]:
        """
        Get the transaction for the user on the given date from the
        Transactions table.

        If the transaction is not found, return None.

        Args:
            user_id: The unique ID of the user.
            date: The date of the transaction.
            transaction_id: The unique ID of the transaction.

        Returns:
            The transaction if found, else None.
        """
        log.info(
            f"Getting transaction '{transaction_id}' on date '{date}' for user from table '{self.table}'"
        )

        transaction = self.ddb.get_item(
            table=self.table,
            key=TransactionsTable._get_transaction_primary_key(
                user_id, date, transaction_id
            ),
        )

        # return None if transaction not found
        if not transaction:
            log.warning(f"Transaction '{transaction_id}' not found for user!")
            return None

        log.info(f"Found transaction '{transaction_id}' on date '{date}' for user!")
        return Transaction.from_ddb_item(transaction)

    def get_transactions(
        self, user_id: str, start_date: dt.datetime, end_date: dt.datetime
    ) -> List[Transaction]:
        """
        Get the transactions for a user in a given date range.

        Args:
            user_id: The unique user ID of the user to get transactions for.
            start_date: The start date of the date range user transactions query.
            end_date:  The end date of the date range user transactions query.

        Returns:
            The list of user transactions over the given date range.
        """
        log.info(f"Getting transactions for user from table '{self.table}'")

        transaction_items = self.ddb.query(
            table=self.table,
            query=TransactionsTable._get_expenses_by_user_id_and_date_range_query(
                user_id, start_date, end_date
            ),
        )

        transactions = [Transaction.from_ddb_item(item) for item in transaction_items]

        log.info(f"Returned {len(transactions)} transactions for user!")
        log.debug(
            f"Transactions:\n{json.dumps([transaction.to_dict() for transaction in transactions], indent=4)}"
        )

        # return transactions sorted by date in descending order
        return sorted(transactions, key=lambda e: e.date, reverse=True)

    def put_transaction(self, transaction: Transaction) -> None:
        log.info("Putting transaction for user to Transactions table")
        log.debug(f"Transaction:\n{json.dumps(transaction.to_dict(), indent=4)}")
        self.ddb.put_item(self.table, transaction.to_ddb_item())

    def delete_transaction(
        self, user_id: str, date: dt.datetime, transaction_id: str
    ) -> None:
        log.info("Deleting transaction for user from Transactions table")
        log.debug(
            f"Transaction:\n{json.dumps({'user_id': user_id, 'date': date.strftime('%Y-%m-%d'), 'transaction_id': transaction_id}, indent=4)}"
        )
        self.ddb.delete_item(
            self.table,
            TransactionsTable._get_transaction_primary_key(
                user_id, date, transaction_id
            ),
        )

    @staticmethod
    def _get_table_name(domain: Domain) -> str:
        return TransactionsTable.TABLE_NAME_FORMAT.format(domain=domain.value)

    @staticmethod
    def _get_expenses_by_user_id_and_date_range_query(
        user_id: str, start_date: dt.datetime, end_date: dt.datetime
    ) -> dict:
        return {
            "user_id": {
                "AttributeValueList": [{"S": user_id}],
                "ComparisonOperator": "EQ",
            },
            "date_uuid": {
                "AttributeValueList": [
                    {"S": f"{start_date.strftime('%Y-%m-%d')}#"},
                    {"S": f"{end_date.strftime('%Y-%m-%d')}#\uffff"},
                ],
                "ComparisonOperator": "BETWEEN",
            },
        }

    @staticmethod
    def _get_transaction_primary_key(
        user_id: str, date: dt.datetime, transaction_id: str
    ) -> dict:
        return {
            "user_id": {"S": user_id},
            "date_uuid": {"S": f"{date.strftime('%Y-%m-%d')}#{transaction_id}"},
        }
