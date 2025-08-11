import datetime
import json
from dataclasses import dataclass

from mypy_boto3_dynamodb.client import DynamoDBClient

from src.database.accounts.models import Account, AccountType
from src.database.stocks.models import Stock
from src.database.users.models import User
from src.database.userstocks.models import UserStock
from src.environment import Domain
from tst.constants import (
    STOCKS_TABLE_NAME,
    USERS_TABLE_NAME,
    USERS_TEST_FILE,
    USERS_STOCKS_TABLE_NAME,
    STOCKS_TEST_FILE,
    USERS_STOCKS_TEST_FILE,
    TRANSACTIONS_TABLE_NAME,
    ACCOUNTS_TABLE_NAME,
    ACCOUNTS_TEST_FILE,
)


@dataclass
class MockDDB:
    """
    MockDDB
    """

    ON_DEMAND_BILLING_MODE = "PAY_PER_REQUEST"

    mock_ddb: DynamoDBClient

    def initialize(self) -> None:
        self._create_stocks_table(STOCKS_TABLE_NAME, STOCKS_TEST_FILE)
        self._create_users_table(USERS_TABLE_NAME, USERS_TEST_FILE)
        self._create_user_stocks_table(USERS_STOCKS_TABLE_NAME, USERS_STOCKS_TEST_FILE)
        self._create_accounts_table(ACCOUNTS_TABLE_NAME, ACCOUNTS_TEST_FILE)
        self._create_transactions_table(TRANSACTIONS_TABLE_NAME)

    def _create_stocks_table(self, table_name: str, input_file_name: str) -> None:
        self.mock_ddb.create_table(
            TableName=table_name,
            KeySchema=[{"AttributeName": "symbol", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "symbol", "AttributeType": "S"}],
            BillingMode=MockDDB.ON_DEMAND_BILLING_MODE,
        )
        with open(input_file_name) as stocks_f:
            for stock in stocks_f:
                if not stock.strip():
                    continue
                json_stock = json.loads(stock)
                self.mock_ddb.put_item(
                    TableName=STOCKS_TABLE_NAME,
                    Item=Stock(
                        symbol=json_stock["symbol"],
                        company=json_stock["company"],
                        description=json_stock["description"],
                        exchange=json_stock["exchange"],
                        sector=json_stock["sector"],
                        industry=json_stock["industry"],
                        official_site=json_stock["official_site"],
                        address=json_stock["address"],
                    ).to_ddb_item(),
                )

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
                        free_trial_end_date=datetime.datetime.strptime(
                            json_user["free_trial_end_date"], "%Y-%m-%dT%H:%M:%SZ"
                        ),
                        stripe_subscription_id=subscription_id,
                        stripe_customer_id=customer_id,
                    ).to_ddb_item(),
                )

    def _create_user_stocks_table(self, table_name: str, input_file_name: str) -> None:
        self.mock_ddb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "user_id", "KeyType": "HASH"},
                {"AttributeName": "stock_symbol", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "user_id", "AttributeType": "S"},
                {"AttributeName": "stock_symbol", "AttributeType": "S"},
            ],
            BillingMode=MockDDB.ON_DEMAND_BILLING_MODE,
        )
        with open(input_file_name) as userstocks_f:
            for userstock in userstocks_f:
                if not userstock.strip():
                    continue
                json_userstock = json.loads(userstock)
                self.mock_ddb.put_item(
                    TableName=USERS_STOCKS_TABLE_NAME,
                    Item=UserStock(
                        user_id=json_userstock["user_id"],
                        stock_symbol=json_userstock["stock_symbol"],
                        quantity=json_userstock["quantity"],
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
            ],
            BillingMode=MockDDB.ON_DEMAND_BILLING_MODE,
        )
        with open(input_file_name) as accounts_f:
            for account in accounts_f:
                if not account.strip():
                    continue
                json_account = json.loads(account)
                self.mock_ddb.put_item(
                    TableName=table_name,
                    Item=Account(
                        user_id=json_account["user_id"],
                        account_id=json_account["account_id"],
                        account_type=AccountType.from_string(
                            json_account["account_type"]
                        ),
                        account_subtype=json_account["account_subtype"],
                        institution_name=json_account["institution_name"],
                        account_name=json_account["account_name"],
                        account_mask=json_account["account_mask"],
                        balance=float(json_account["balance"]),
                        created_at=datetime.datetime.strptime(
                            json_account["created_at"], "%Y-%m-%dT%H:%M:%SZ"
                        ),
                        updated_at=datetime.datetime.strptime(
                            json_account["updated_at"], "%Y-%m-%dT%H:%M:%SZ"
                        ),
                        logo_url=json_account["logo_url"],
                    ).to_ddb_item(),
                )

    def _create_transactions_table(self, table_name: str) -> None:
        self.mock_ddb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "user_id", "KeyType": "HASH"},
                {"AttributeName": "date_uuid", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "user_id", "AttributeType": "S"},
                {"AttributeName": "date_uuid", "AttributeType": "S"},
            ],
            BillingMode=MockDDB.ON_DEMAND_BILLING_MODE,
        )
