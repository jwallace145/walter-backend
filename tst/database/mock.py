import datetime
import json
from dataclasses import dataclass

from mypy_boto3_dynamodb.client import DynamoDBClient

from src.database.accounts.models import Account, AccountType
from src.database.securities.models import SecurityType, Stock, Crypto
from src.database.users.models import User
from src.environment import Domain
from tst.constants import (
    USERS_TABLE_NAME,
    USERS_TEST_FILE,
    TRANSACTIONS_TABLE_NAME,
    ACCOUNTS_TABLE_NAME,
    ACCOUNTS_TEST_FILE,
    SECURITIES_TABLE_NAME,
    SECURITIES_TEST_FILE,
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
        self._create_accounts_table(ACCOUNTS_TABLE_NAME, ACCOUNTS_TEST_FILE)
        self._create_securities_table(SECURITIES_TABLE_NAME, SECURITIES_TEST_FILE)
        self._create_transactions_table(TRANSACTIONS_TABLE_NAME)

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

    def _create_securities_table(self, table_name: str, input_file_name: str) -> None:
        self.mock_ddb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "security_id", "KeyType": "HASH"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "security_id", "AttributeType": "S"},
            ],
            BillingMode=MockDDB.ON_DEMAND_BILLING_MODE,
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
                            price_updated_at=datetime.datetime.strptime(
                                security_json["price_updated_at"], "%Y-%m-%dT%H:%M:%SZ"
                            ),
                            price_expires_at=datetime.datetime.strptime(
                                security_json["price_expires_at"], "%Y-%m-%dT%H:%M:%SZ"
                            ),
                            security_id=security_json["security_id"],
                        )
                    case SecurityType.CRYPTO:
                        security = Crypto(
                            name=security_json["security_name"],
                            ticker=security_json["ticker"],
                            price=float(security_json["current_price"]),
                            price_updated_at=datetime.datetime.strptime(
                                security_json["price_updated_at"], "%Y-%m-%dT%H:%M:%SZ"
                            ),
                            price_expires_at=datetime.datetime.strptime(
                                security_json["price_expires_at"], "%Y-%m-%dT%H:%M:%SZ"
                            ),
                            security_id=security_json["security_id"],
                        )
                    case _:
                        raise ValueError(f"Invalid security type: {security_type}")
                self.mock_ddb.put_item(
                    TableName=table_name,
                    Item=security.to_ddb_item(),
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
