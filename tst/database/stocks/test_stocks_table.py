import boto3
import pytest
from moto import mock_aws
from mypy_boto3_dynamodb.client import DynamoDBClient

from src.database.client import WalterDDBClient
from src.database.stocks.table import StocksTable
from src.environment import Domain


@pytest.fixture
def ddb_client() -> DynamoDBClient:
    with mock_aws():
        mock_ddb = boto3.client("dynamodb", region_name="us-east-1")
        mock_ddb.create_table(
            TableName="Stocks-unittest",
            KeySchema=[{"AttributeName": "symbol", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "symbol", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        mock_ddb.put_item(
            TableName="Stocks-unittest",
            Item={
                "symbol": {
                    "S": "AAPL",
                },
                "company": {"S": "Apple"},
            },
        )
        yield mock_ddb


@pytest.fixture
def walter_ddb_client(ddb_client) -> WalterDDBClient:
    return WalterDDBClient(ddb_client)


@pytest.fixture
def stocks_table(walter_ddb_client) -> StocksTable:
    return StocksTable(walter_ddb_client, Domain.TESTING)


def test_list_stocks(stocks_table) -> None:
    stocks = stocks_table.list_stocks()
    assert len(stocks) == 1
    assert stocks[0].symbol == "AAPL"
    assert stocks[0].company == "Apple"
