import datetime
import json
from dataclasses import dataclass

from mypy_boto3_dynamodb.client import DynamoDBClient

from src.database.accounts.models import Account
from src.database.holdings.models import Holding
from src.database.securities.models import Crypto, SecurityType, Stock
from src.database.sessions.models import Session
from src.database.transactions.models import (
    BankingTransactionSubType,
    BankTransaction,
    InvestmentTransaction,
    InvestmentTransactionSubType,
    TransactionCategory,
    TransactionType,
)
from src.database.users.models import User
from src.environment import Domain
from tst.constants import (
    ACCOUNTS_TABLE_NAME,
    ACCOUNTS_TEST_FILE,
    HOLDINGS_TABLE_NAME,
    HOLDINGS_TEST_FILE,
    SECURITIES_TABLE_NAME,
    SECURITIES_TEST_FILE,
    SESSIONS_TABLE_NAME,
    SESSIONS_TEST_FILE,
    TRANSACTIONS_TABLE_NAME,
    TRANSACTIONS_TEST_FILE,
    USERS_TABLE_NAME,
    USERS_TEST_FILE,
)


@dataclass
class MockDDB:
    """
    MockDDB
    """

    ON_DEMAND_BILLING_MODE = "PAY_PER_REQUEST"

    mock_ddb: DynamoDBClient

    def initialize(self) -> None:
        self._create_users_table(USERS_TABLE_NAME, USERS_TEST_FILE)
        self._create_sessions_table(SESSIONS_TABLE_NAME, SESSIONS_TEST_FILE)
        self._create_accounts_table(ACCOUNTS_TABLE_NAME, ACCOUNTS_TEST_FILE)
        self._create_securities_table(SECURITIES_TABLE_NAME, SECURITIES_TEST_FILE)
        self._create_holdings_table(HOLDINGS_TABLE_NAME, HOLDINGS_TEST_FILE)
        self._create_transactions_table(TRANSACTIONS_TABLE_NAME, TRANSACTIONS_TEST_FILE)

    def _create_users_table(self, table_name: str, input_file_name: str) -> None:
        self.mock_ddb.create_table(
            TableName=table_name,
            KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "user_id", "AttributeType": "S"},
                {"AttributeName": "email", "AttributeType": "S"},
            ],
            BillingMode=MockDDB.ON_DEMAND_BILLING_MODE,
            GlobalSecondaryIndexes=[
                {
                    "IndexName": f"Users-EmailIndex-{Domain.TESTING.value}",
                    "KeySchema": [{"AttributeName": "email", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
        )
        with open(input_file_name) as users_f:
            for user in users_f:
                if not user.strip():
                    continue
                json_user = json.loads(user)
                subscription_id = None
                if json_user["stripe_subscription_id"] != "N/A":
                    subscription_id = json_user["stripe_subscription_id"]
                customer_id = None
                if json_user["stripe_customer_id"] != "N/A":
                    customer_id = json_user["stripe_customer_id"]
                self.mock_ddb.put_item(
                    TableName=USERS_TABLE_NAME,
                    Item=User(
                        user_id=json_user["user_id"],
                        email=json_user["email"],
                        first_name=json_user["first_name"],
                        last_name=json_user["last_name"],
                        password_hash=json_user["password_hash"],
                        verified=json_user["verified"],
                        sign_up_date=datetime.datetime.strptime(
                            json_user["sign_up_date"], "%Y-%m-%dT%H:%M:%SZ"
                        ),
                        stripe_subscription_id=subscription_id,
                        stripe_customer_id=customer_id,
                    ).to_ddb_item(),
                )

    def _create_sessions_table(self, table_name: str, input_file_name: str) -> None:
        self.mock_ddb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "user_id", "KeyType": "HASH"},
                {"AttributeName": "token_id", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "user_id", "AttributeType": "S"},
                {"AttributeName": "token_id", "AttributeType": "S"},
            ],
            BillingMode=MockDDB.ON_DEMAND_BILLING_MODE,
        )
        with open(input_file_name) as sessions_f:
            for session in sessions_f:
                if not session.strip():
                    continue
                json_session = json.loads(session)
                self.mock_ddb.put_item(
                    TableName=table_name,
                    Item=Session(
                        user_id=json_session["user_id"],
                        token_id=json_session["token_id"],
                        ip_address=json_session["ip_address"],
                        device=json_session["device"],
                        session_start=datetime.datetime.fromisoformat(
                            json_session["session_start"]
                        ),
                        session_expiration=datetime.datetime.fromisoformat(
                            json_session["session_expiration"]
                        ),
                        revoked=json_session["revoked"],
                        session_end=None,
                    ).to_ddb_item(),
                )

    def _create_accounts_table(self, table_name: str, input_file_name: str) -> None:
        self.mock_ddb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "user_id", "KeyType": "HASH"},
                {"AttributeName": "account_id", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "user_id", "AttributeType": "S"},
                {"AttributeName": "account_id", "AttributeType": "S"},
                {"AttributeName": "plaid_item_id", "AttributeType": "S"},
                {"AttributeName": "plaid_account_id", "AttributeType": "S"},
            ],
            BillingMode=MockDDB.ON_DEMAND_BILLING_MODE,
            GlobalSecondaryIndexes=[
                {
                    "IndexName": f"Accounts-PlaidItemIdIndex-{Domain.TESTING.value}",
                    "KeySchema": [
                        {"AttributeName": "plaid_item_id", "KeyType": "HASH"}
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
                {
                    "IndexName": f"Accounts-PlaidAccountIdIndex-{Domain.TESTING.value}",
                    "KeySchema": [
                        {"AttributeName": "plaid_account_id", "KeyType": "HASH"}
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
            ],
        )
        with open(input_file_name) as accounts_f:
            for account in accounts_f:
                if not account.strip():
                    continue
                json_account = json.loads(account)
                account_item = Account.from_ddb_item(
                    {
                        "account_id": {
                            "S": json_account["account_id"],
                        },
                        "user_id": {
                            "S": json_account["user_id"],
                        },
                        "account_type": {
                            "S": json_account["account_type"],
                        },
                        "account_subtype": {
                            "S": json_account["account_subtype"],
                        },
                        "institution_name": {
                            "S": json_account["institution_name"],
                        },
                        "account_name": {
                            "S": json_account["account_name"],
                        },
                        "account_mask": {
                            "S": json_account["account_mask"],
                        },
                        "balance": {
                            "N": str(json_account["balance"]),
                        },
                        "balance_last_updated_at": {
                            "S": json_account["balance_last_updated_at"],
                        },
                        "created_at": {
                            "S": json_account["created_at"],
                        },
                        "updated_at": {
                            "S": json_account["updated_at"],
                        },
                        "logo_url": {
                            "S": json_account["logo_url"],
                        },
                        "plaid_account_id": {
                            "S": json_account["plaid_account_id"],
                        },
                        "plaid_item_id": {
                            "S": json_account["plaid_item_id"],
                        },
                        "plaid_access_token": {
                            "S": json_account["plaid_access_token"],
                        },
                    }
                ).to_ddb_item()
                self.mock_ddb.put_item(
                    TableName=table_name,
                    Item=account_item,
                )

    def _create_securities_table(self, table_name: str, input_file_name: str) -> None:
        self.mock_ddb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "security_id", "KeyType": "HASH"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "security_id", "AttributeType": "S"},
                {"AttributeName": "ticker", "AttributeType": "S"},
            ],
            BillingMode=MockDDB.ON_DEMAND_BILLING_MODE,
            GlobalSecondaryIndexes=[
                {
                    "IndexName": f"Securities-TickerIndex-{Domain.TESTING.value}",
                    "KeySchema": [{"AttributeName": "ticker", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
        )
        with open(input_file_name) as securities_f:
            for security_jsonl in securities_f:
                if not security_jsonl.strip():
                    continue
                security_json = json.loads(security_jsonl)
                security_type = SecurityType.from_string(security_json["security_type"])
                match security_type:
                    case SecurityType.STOCK:
                        security = Stock(
                            name=security_json["security_name"],
                            ticker=security_json["ticker"],
                            exchange=security_json["exchange"],
                            price=float(security_json["current_price"]),
                            price_updated_at=datetime.datetime.fromisoformat(
                                security_json["price_updated_at"]
                            ),
                            price_expires_at=datetime.datetime.fromisoformat(
                                security_json["price_expires_at"]
                            ),
                            security_id=security_json["security_id"],
                        )
                    case SecurityType.CRYPTO:
                        security = Crypto(
                            name=security_json["security_name"],
                            ticker=security_json["ticker"],
                            price=float(security_json["current_price"]),
                            price_updated_at=datetime.datetime.fromisoformat(
                                security_json["price_updated_at"]
                            ),
                            price_expires_at=datetime.datetime.fromisoformat(
                                security_json["price_expires_at"]
                            ),
                            security_id=security_json["security_id"],
                        )
                    case _:
                        raise ValueError(f"Invalid security type: {security_type}")
                self.mock_ddb.put_item(
                    TableName=table_name,
                    Item=security.to_ddb_item(),
                )

    def _create_holdings_table(self, table_name: str, input_file_name: str) -> None:
        self.mock_ddb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "account_id", "KeyType": "HASH"},
                {"AttributeName": "security_id", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "account_id", "AttributeType": "S"},
                {"AttributeName": "security_id", "AttributeType": "S"},
            ],
            BillingMode=MockDDB.ON_DEMAND_BILLING_MODE,
        )
        with open(input_file_name) as holdings_f:
            for holding in holdings_f:
                if not holding.strip():
                    continue
                holding_json = json.loads(holding)
                self.mock_ddb.put_item(
                    TableName=table_name,
                    Item=Holding(
                        account_id=holding_json["account_id"],
                        security_id=holding_json["security_id"],
                        quantity=float(holding_json["quantity"]),
                        total_cost_basis=float(holding_json["total_cost_basis"]),
                        average_cost_basis=float(holding_json["average_cost_basis"]),
                        created_at=datetime.datetime.strptime(
                            holding_json["created_at"], "%Y-%m-%dT%H:%M:%SZ"
                        ),
                        updated_at=datetime.datetime.strptime(
                            holding_json["updated_at"], "%Y-%m-%dT%H:%M:%SZ"
                        ),
                    ).to_ddb_item(),
                )

    def _create_transactions_table(self, table_name: str, input_file_name: str) -> None:
        self.mock_ddb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "account_id", "KeyType": "HASH"},
                {"AttributeName": "transaction_date", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "user_id", "AttributeType": "S"},
                {"AttributeName": "account_id", "AttributeType": "S"},
                {"AttributeName": "transaction_date", "AttributeType": "S"},
            ],
            BillingMode=MockDDB.ON_DEMAND_BILLING_MODE,
            GlobalSecondaryIndexes=[
                {
                    "IndexName": f"Transactions-UserIndex-{Domain.TESTING.value}",
                    "KeySchema": [
                        {"AttributeName": "user_id", "KeyType": "HASH"},
                        {"AttributeName": "transaction_date", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
        )
        # seed transactions from the provided JSONL file
        with open(input_file_name) as transactions_f:
            for txn in transactions_f:
                if not txn.strip():
                    continue
                transaction_json = json.loads(txn)
                transaction_id = transaction_json["transaction_id"]
                transaction_item = None
                if transaction_id.startswith("investment"):
                    transaction_item = InvestmentTransaction(
                        user_id=transaction_json["user_id"],
                        account_id=transaction_json["account_id"],
                        transaction_type=TransactionType.from_string(
                            transaction_json["transaction_type"]
                        ),
                        transaction_subtype=InvestmentTransactionSubType.from_string(
                            transaction_json["transaction_subtype"]
                        ),
                        transaction_category=TransactionCategory.from_string(
                            transaction_json["transaction_category"]
                        ),
                        transaction_date=datetime.datetime.strptime(
                            transaction_json["transaction_date"], "%Y-%m-%d"
                        ),
                        transaction_amount=float(
                            transaction_json["transaction_amount"]
                        ),
                        security_id=transaction_json["security_id"],
                        quantity=float(transaction_json["quantity"]),
                        price_per_share=float(transaction_json["price_per_share"]),
                        transaction_id=transaction_id,
                        plaid_account_id=transaction_json["plaid_account_id"],
                        plaid_transaction_id=transaction_json["plaid_transaction_id"],
                    ).to_ddb_item()
                else:
                    transaction_item = BankTransaction(
                        user_id=transaction_json["user_id"],
                        account_id=transaction_json["account_id"],
                        transaction_type=TransactionType.from_string(
                            transaction_json["transaction_type"]
                        ),
                        transaction_subtype=BankingTransactionSubType.from_string(
                            transaction_json["transaction_subtype"]
                        ),
                        transaction_category=TransactionCategory.from_string(
                            transaction_json["transaction_category"]
                        ),
                        transaction_date=datetime.datetime.strptime(
                            transaction_json["transaction_date"], "%Y-%m-%d"
                        ),
                        transaction_amount=float(
                            transaction_json["transaction_amount"]
                        ),
                        merchant_name=transaction_json["merchant_name"],
                        transaction_id=transaction_id,
                        plaid_account_id=transaction_json["plaid_account_id"],
                        plaid_transaction_id=transaction_json["plaid_transaction_id"],
                    ).to_ddb_item()
                self.mock_ddb.put_item(TableName=table_name, Item=transaction_item)
