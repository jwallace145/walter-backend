from typing import List

import boto3
import pytest
from moto import mock_aws
from mypy_boto3_dynamodb import DynamoDBClient

from src.database.client import WalterDDBClient
from src.database.stocks.models import Stock
from src.database.stocks.table import StocksTable
from src.database.users.models import User
from src.database.users.table import UsersTable
from src.database.userstocks.table import UsersStocksTable
from src.environment import Domain


@pytest.fixture(scope="session")
def users() -> List[User]:
    return [User(email="walteraifinancialadvisor@gmail.com", username="walter")]


@pytest.fixture(scope="session")
def stocks() -> List[Stock]:
    return [Stock(symbol="AAPL", company="Apple")]


@pytest.fixture(scope="session")
def ddb_client(users: List[User], stocks: List[Stock]) -> DynamoDBClient:
    with mock_aws():
        mock_ddb = boto3.client("dynamodb", region_name="us-east-1")

        # create stocks table
        mock_ddb.create_table(
            TableName="Stocks-unittest",
            KeySchema=[{"AttributeName": "symbol", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "symbol", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        mock_ddb.put_item(
            TableName="Stocks-unittest",
            Item=stocks[0].to_ddb_item(),
        )

        # create users table
        mock_ddb.create_table(
            TableName="Users-unittest",
            KeySchema=[{"AttributeName": "email", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "email", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        mock_ddb.put_item(
            TableName="Users-unittest",
            Item=users[0].to_ddb_item(),
        )

        # create user stocks table
        mock_ddb.create_table(
            TableName="UsersStocks-unittest",
            KeySchema=[{"AttributeName": "user_email", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "user_email", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        mock_ddb.put_item(
            TableName="UsersStocks-unittest",
            Item={
                "user_email": {
                    "S": "walteraifinancialadvisor@gmail.com",
                },
                "stock_symbol": {"S": "AAPL"},
            },
        )

        yield mock_ddb


@pytest.fixture(scope="session")
def walter_ddb_client(ddb_client) -> WalterDDBClient:
    return WalterDDBClient(ddb_client)


@pytest.fixture(scope="session")
def stocks_table(walter_ddb_client) -> StocksTable:
    return StocksTable(walter_ddb_client, Domain.TESTING)


@pytest.fixture(scope="session")
def users_table(walter_ddb_client) -> UsersTable:
    return UsersTable(walter_ddb_client, Domain.TESTING)


@pytest.fixture(scope="session")
def users_stocks_table(walter_ddb_client) -> UsersStocksTable:
    return UsersStocksTable(walter_ddb_client, Domain.TESTING)
