import json
import os

import boto3
import pytest
from moto import mock_aws
from mypy_boto3_dynamodb import DynamoDBClient
from mypy_boto3_secretsmanager import SecretsManagerClient
from mypy_boto3_sqs import SQSClient

from src.aws.dynamodb.client import WalterDDBClient
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.aws.sqs.client import WalterSQSClient
from src.database.client import WalterDB
from src.database.stocks.models import Stock
from src.database.users.models import User
from src.database.userstocks.models import UserStock
from src.environment import Domain
from src.newsletters.queue import NewslettersQueue
from src.utils.auth import generate_token

#############
# CONSTANTS #
#############

AWS_REGION = "us-east-1"

SECRETS_MANAGER_POLYGON_API_KEY_NAME = "PolygonAPIKey"
SECRETS_MANAGER_POLYGON_API_KEY_VALUE = "test-polygon-api-key"

SECRETS_MANAGER_JWT_SECRET_KEY_SECRET_NAME = "JWTSecretKey"
SECRETS_MANAGER_JWT_SECRET_KEY_SECRET_VALUE = "test-jwt-secret-key"

STOCKS_TABLE_NAME = "Stocks-unittest"
USERS_TABLE_NAME = "Users-unittest"
USERS_STOCKS_TABLE_NAME = "UsersStocks-unittest"

NEWSLETTERS_QUEUE_NAME = "NewslettersQueue-unittest"

STOCKS_TEST_FILE = "tst/database/data/stocks.jsonl"
USERS_TEST_FILE = "tst/database/data/users.jsonl"
USERS_STOCKS_TEST_FILE = "tst/database/data/usersstocks.jsonl"

###################
# GLOBAL FIXTURES #
###################


@pytest.fixture
def ddb_client() -> DynamoDBClient:
    with mock_aws():
        mock_ddb = boto3.client("dynamodb", region_name=AWS_REGION)

        # create stocks table
        mock_ddb.create_table(
            TableName=STOCKS_TABLE_NAME,
            KeySchema=[{"AttributeName": "symbol", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "symbol", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        with open(STOCKS_TEST_FILE) as stocks_f:
            for stock in stocks_f:
                if not stock.strip():
                    continue
                json_stock = json.loads(stock)
                mock_ddb.put_item(
                    TableName=STOCKS_TABLE_NAME,
                    Item=Stock(
                        symbol=json_stock["symbol"], company=json_stock["company"]
                    ).to_ddb_item(),
                )

        # create users table
        mock_ddb.create_table(
            TableName=USERS_TABLE_NAME,
            KeySchema=[{"AttributeName": "email", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "email", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        with open(USERS_TEST_FILE) as users_f:
            for user in users_f:
                if not user.strip():
                    continue
                json_user = json.loads(user)
                mock_ddb.put_item(
                    TableName=USERS_TABLE_NAME,
                    Item=User(
                        email=json_user["email"],
                        username=json_user["username"],
                        password_hash=json_user["password_hash"]
                    ).to_ddb_item(),
                )

        # create user stocks table
        mock_ddb.create_table(
            TableName=USERS_STOCKS_TABLE_NAME,
            KeySchema=[
                {"AttributeName": "user_email", "KeyType": "HASH"},
                {"AttributeName": "stock_symbol", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "user_email", "AttributeType": "S"},
                {"AttributeName": "stock_symbol", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        with open(USERS_STOCKS_TEST_FILE) as userstocks_f:
            for userstock in userstocks_f:
                if not userstock.strip():
                    continue
                json_userstock = json.loads(userstock)
                mock_ddb.put_item(
                    TableName=USERS_STOCKS_TABLE_NAME,
                    Item=UserStock(
                        user_email=json_userstock["user_email"],
                        stock_symbol=json_userstock["stock_symbol"],
                        quantity=json_userstock["quantity"],
                    ).to_ddb_item(),
                )

        yield mock_ddb


@pytest.fixture
def secrets_manager_client() -> SecretsManagerClient:
    with mock_aws():
        mock_secrets_manager = boto3.client("secretsmanager", region_name=AWS_REGION)
        mock_secrets_manager.create_secret(
            Name=SECRETS_MANAGER_POLYGON_API_KEY_NAME,
            SecretString=json.dumps(
                {"POLYGON_API_KEY": SECRETS_MANAGER_POLYGON_API_KEY_VALUE}
            ),
        )
        mock_secrets_manager.create_secret(
            Name=SECRETS_MANAGER_JWT_SECRET_KEY_SECRET_NAME,
            SecretString=json.dumps(
                {"JWT_SECRET_KEY": SECRETS_MANAGER_JWT_SECRET_KEY_SECRET_VALUE}
            ),
        )
        yield mock_secrets_manager


@pytest.fixture
def sqs_client() -> SQSClient:
    with mock_aws():
        mock_sqs = boto3.client("sqs", region_name=AWS_REGION)
        mock_sqs.create_queue(QueueName=NEWSLETTERS_QUEUE_NAME)
        yield mock_sqs


@pytest.fixture(autouse=True)
def env_vars():
    os.environ["AWS_ACCOUNT_ID"] = "012345678901"
    yield
    del os.environ["AWS_ACCOUNT_ID"]


@pytest.fixture
def walter_db(ddb_client) -> WalterDB:
    return WalterDB(ddb=WalterDDBClient(ddb_client), domain=Domain.TESTING)


@pytest.fixture
def walter_sm(
    secrets_manager_client: SecretsManagerClient,
) -> WalterSecretsManagerClient:
    return WalterSecretsManagerClient(
        client=secrets_manager_client, domain=Domain.TESTING
    )


@pytest.fixture
def newsletters_queue(sqs_client) -> NewslettersQueue:
    return NewslettersQueue(
        client=WalterSQSClient(client=sqs_client, domain=Domain.TESTING)
    )


@pytest.fixture
def jwt_walter(walter_sm: WalterSecretsManagerClient) -> str:
    return generate_token("walter@gmail.com", walter_sm.get_jwt_secret_key())


@pytest.fixture
def jwt_walrus(walter_sm: WalterSecretsManagerClient) -> str:
    return generate_token("walrus@gmail.com", walter_sm.get_jwt_secret_key())
