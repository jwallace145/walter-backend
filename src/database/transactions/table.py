import json
from dataclasses import dataclass
from typing import List

from src.aws.dynamodb.client import WalterDDBClient
from src.database.transactions.models import Transaction, TransactionCategory
from src.environment import Domain
from src.utils.log import Logger
import datetime as dt

log = Logger(__name__).get_logger()


@dataclass
class TransactionsTable:

    TABLE_NAME_FORMAT = "Transactions-{domain}"

    ddb: WalterDDBClient
    domain: Domain

    table: str = None  # set during post init

    def __post_init__(self) -> None:
        self.table = TransactionsTable._get_table_name(self.domain)
        log.debug(f"Creating ExpensesTable DDB client with table name '{self.table}'")

    def get_transactions(
        self, user_id: str, start_date: dt.datetime, end_date: dt.datetime
    ) -> List[Transaction]:
        log.info(f"Getting transactions for user from table '{self.table}'")

        transaction_items = self.ddb.query(
            table=self.table,
            query=TransactionsTable._get_expenses_by_user_id_and_date_range_query(
                user_id, start_date, end_date
            ),
        )

        transactions = []
        for item in transaction_items:
            transactions.append(TransactionsTable._get_transaction_from_ddb_item(item))

        log.info(f"Returned {len(transactions)} expenses for user!")

        # return expenses sorted by date in descending order
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
            f"Expense:\n{json.dumps({'user_id': user_id, 'date': date.strftime('%Y-%m-%d'), 'transaction_id': transaction_id}, indent=4)}"
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

    @staticmethod
    def _get_transaction_from_ddb_item(item: dict) -> Transaction:
        date_uuid = item["date_uuid"]["S"]
        date_str, transaction_id = date_uuid.split("#")
        date = dt.datetime.strptime(date_str, "%Y-%m-%d")
        amount = float(item["amount"]["S"])
        category = TransactionCategory.from_string(item["category"]["S"])
        return Transaction(
            user_id=item["user_id"]["S"],
            date=date,
            vendor=item["vendor"]["S"],
            amount=amount,
            category=category,
            transaction_id=transaction_id,
            date_uuid=date_uuid,
        )
