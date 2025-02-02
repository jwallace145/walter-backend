import json
import os
from datetime import datetime as dt, timedelta
from typing import List

import boto3
import pytest
from moto import mock_aws
from mypy_boto3_cloudwatch import CloudWatchClient
from mypy_boto3_dynamodb import DynamoDBClient
from mypy_boto3_s3.client import S3Client
from mypy_boto3_secretsmanager import SecretsManagerClient
from mypy_boto3_ses.client import SESClient
from mypy_boto3_sqs import SQSClient
from polygon import RESTClient, BadResponse
from polygon.rest.models import Agg, TickerNews, TickerDetails

from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.dynamodb.client import WalterDDBClient
from src.aws.s3.client import WalterS3Client
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.aws.ses.client import WalterSESClient
from src.aws.sqs.client import WalterSQSClient
from src.database.client import WalterDB
from src.database.stocks.models import Stock
from src.database.users.models import User
from src.database.userstocks.models import UserStock
from src.environment import Domain
from src.newsletters.queue import NewslettersQueue
from src.stocks.alphavantage.models import CompanyOverview
from src.stocks.client import WalterStocksAPI
from src.stocks.polygon.client import PolygonClient
from src.templates.bucket import TemplatesBucket
from src.templates.engine import TemplatesEngine

#############
# CONSTANTS #
#############

AWS_REGION = "us-east-1"

SECRETS_MANAGER_ALPHA_VANTAGE_API_KEY_NAME = "AlphaVantageAPIKey"
SECRETS_MANAGER_ALPHA_VANTAGE_API_KEY_VALUE = "test-alpha-vantage-api-key"

SECRETS_MANAGER_POLYGON_API_KEY_NAME = "PolygonAPIKey"
SECRETS_MANAGER_POLYGON_API_KEY_VALUE = "test-polygon-api-key"

SECRETS_MANAGER_JWT_SECRET_KEY_SECRET_NAME = "JWTSecretKey"
SECRETS_MANAGER_JWT_SECRET_KEY_SECRET_VALUE = "test-jwt-secret-key"

SECRETS_MANAGER_CHANGE_PASSWORD_KEY_SECRET_NAME = "JWTChangePasswordSecretKey"
SECRETS_MANAGER_CHANGE_PASSWORD_KEY_SECRET_VALUE = "test-change-password-key"

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
                        password_hash=json_user["password_hash"],
                        verified=json_user["verified"],
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
        mock_secrets_manager.create_secret(
            Name=SECRETS_MANAGER_CHANGE_PASSWORD_KEY_SECRET_NAME,
            SecretString=json.dumps(
                {
                    "JWT_CHANGE_PASSWORD_SECRET_KEY": SECRETS_MANAGER_CHANGE_PASSWORD_KEY_SECRET_VALUE
                }
            ),
        )
        yield mock_secrets_manager


@pytest.fixture
def cloud_watch_client() -> CloudWatchClient:
    with mock_aws():
        mock_cloudwatch = boto3.client("cloudwatch", region_name=AWS_REGION)
        yield mock_cloudwatch


@pytest.fixture
def sqs_client() -> SQSClient:
    with mock_aws():
        mock_sqs = boto3.client("sqs", region_name=AWS_REGION)
        mock_sqs.create_queue(QueueName=NEWSLETTERS_QUEUE_NAME)
        yield mock_sqs


@pytest.fixture
def s3_client() -> S3Client:
    with mock_aws():
        mock_s3 = boto3.client("s3", region_name=AWS_REGION)
        mock_s3.create_bucket(Bucket="walterai-templates-unittest")
        mock_s3.put_object(
            Bucket="walterai-templates-unittest",
            Key="templates/default/templatespec.jinja",
            Body=open("./templates/default/templatespec.jinja", "rb").read(),
        )
        mock_s3.put_object(
            Bucket="walterai-templates-unittest",
            Key="templates/default/template.jinja",
            Body=open("./templates/default/template.jinja", "rb").read(),
        )
        yield mock_s3


@pytest.fixture
def ses_client() -> S3Client:
    with mock_aws():
        mock_ses = boto3.client("ses", region_name=AWS_REGION)
        yield mock_ses


@pytest.fixture(autouse=True)
def env_vars():
    os.environ["AWS_ACCOUNT_ID"] = "012345678901"
    yield
    del os.environ["AWS_ACCOUNT_ID"]


@pytest.fixture
def walter_stocks_api(mocker) -> WalterStocksAPI:
    mock_polygon_rest_client = mocker.MagicMock(spec=RESTClient)

    start_date = dt(
        year=2024, month=10, day=1, hour=0, minute=0, second=0, microsecond=0
    )
    end_date = dt(year=2024, month=10, day=1, hour=2, minute=0, second=0, microsecond=0)

    aapl = Stock(
        symbol="AAPL", company="Apple Inc.", sector="Technology", industry="Electronics"
    )
    meta = Stock(
        symbol="META", company="Meta", sector="Technology", industry="Electronics"
    )
    abnb = Stock(
        symbol="ABNB",
        company="Airbnb",
        exchange="NYSE",
        sector="Trade & Services",
        industry="Lodging",
        official_site="https://walterai.dev",
    )

    def mock_aggs(*args, **kwargs) -> List[Agg]:
        aggs = {
            aapl.symbol: [
                Agg(
                    open=90.0,
                    high=100.0,
                    low=85.0,
                    close=95.0,
                    timestamp=start_date.timestamp() * 1000,
                ),
                Agg(
                    open=95.0,
                    high=100.0,
                    low=90.0,
                    close=100.0,
                    timestamp=(start_date + timedelta(hours=1)).timestamp() * 1000,
                ),
                Agg(
                    open=100.0,
                    high=120.0,
                    low=95.0,
                    close=105.0,
                    timestamp=end_date.timestamp() * 1000,
                ),
            ],
            meta.symbol: [
                Agg(
                    open=200.0,
                    high=220.0,
                    low=190.0,
                    close=210.0,
                    timestamp=start_date.timestamp() * 1000,
                ),
                Agg(
                    open=225.0,
                    high=240.0,
                    low=220.0,
                    close=230.0,
                    timestamp=(start_date + timedelta(hours=1)).timestamp() * 1000,
                ),
                Agg(
                    open=250.0,
                    high=255.0,
                    low=245.0,
                    close=250.0,
                    timestamp=end_date.timestamp() * 1000,
                ),
            ],
        }
        for key, value in kwargs.items():
            if key == "ticker":
                return aggs[value]
        raise ValueError("ticker not in get aggs kwargs!")

    mock_polygon_rest_client.list_aggs.side_effect = mock_aggs

    def mock_ticker_news(*args, **kwargs) -> List[TickerNews]:
        news = {
            aapl.symbol: [
                TickerNews(
                    author="Maya Grayson",
                    title="Scientists Discover Hidden Underwater City Off the Coast of Australia",
                    description="It is much bigger than Atlantis!",
                )
            ],
            meta.symbol: [
                TickerNews(
                    author="Ethan Caldwell",
                    title="Local Bakery Breaks World Record for Largest Croissant Ever Made",
                    description="The croissant weights over 500 pounds!",
                ),
                TickerNews(
                    author="Lila Montgomery",
                    title="Tech Giant Unveils Revolutionary Smart Glasses That Can Read Your Thoughts",
                    description="Uh oh, a lot of people are going to be in trouble!",
                ),
            ],
        }
        for key, value in kwargs.items():
            if key == "ticker":
                return news[value]
        raise ValueError("ticker not in list ticker news kwargs!")

    mock_polygon_rest_client.list_ticker_news.side_effect = mock_ticker_news

    def mock_get_ticker_details(*args, **kwargs) -> TickerDetails:
        details = {
            aapl.symbol: TickerDetails(
                ticker=aapl.symbol,
                name=aapl.company,
            ),
            meta.symbol: TickerDetails(
                ticker=meta.symbol,
                name=meta.company,
            ),
            abnb.symbol: TickerDetails(
                ticker=abnb.symbol,
                name=abnb.company,
            ),
        }
        for key, value in kwargs.items():
            if key == "ticker":
                try:
                    return details[value]
                except KeyError:
                    raise BadResponse("Stock not found!")
        raise ValueError("ticker not in get ticket details kwargs!")

    mock_polygon_rest_client.get_ticker_details.side_effect = mock_get_ticker_details

    class MockAlphaVantageClient:
        def __init__(self):
            self.company_overview_map = {
                aapl.symbol: CompanyOverview(
                    symbol=aapl.symbol,
                    name=aapl.company,
                    description=aapl.company,
                    exchange="NYSE",
                    sector=aapl.sector,
                    industry=aapl.industry,
                    official_site="https://walterai.dev",
                    address=aapl.address,
                ),
                meta.symbol: CompanyOverview(
                    symbol=meta.symbol,
                    name=meta.company,
                    description=meta.company,
                    exchange="NYSE",
                    sector=meta.sector,
                    industry=meta.industry,
                    official_site="https://walterai.dev",
                    address=meta.address,
                ),
                abnb.symbol: CompanyOverview(
                    symbol=abnb.symbol,
                    name=abnb.company,
                    description=abnb.company,
                    exchange="NYSE",
                    sector=abnb.sector,
                    industry=abnb.industry,
                    official_site="https://walterai.dev",
                    address=abnb.address,
                ),
            }

        def get_company_overview(self, symbol: str) -> CompanyOverview:
            return self.company_overview_map.get(symbol)

    return WalterStocksAPI(
        polygon=PolygonClient(
            api_key=SECRETS_MANAGER_POLYGON_API_KEY_VALUE,
            client=mock_polygon_rest_client,
        ),
        alpha_vantage=MockAlphaVantageClient(),
    )


@pytest.fixture
def walter_sm(
    secrets_manager_client: SecretsManagerClient,
) -> WalterSecretsManagerClient:
    return WalterSecretsManagerClient(
        client=secrets_manager_client, domain=Domain.TESTING
    )


@pytest.fixture
def walter_s3(s3_client: S3Client) -> WalterS3Client:
    return WalterS3Client(client=s3_client, domain=Domain.TESTING)


@pytest.fixture
def walter_ses(ses_client: SESClient) -> WalterSESClient:
    return WalterSESClient(client=ses_client, domain=Domain.TESTING)


@pytest.fixture
def walter_authenticator(walter_sm: WalterSecretsManagerClient) -> WalterAuthenticator:
    return WalterAuthenticator(walter_sm=walter_sm)


@pytest.fixture
def walter_db(ddb_client, walter_authenticator: WalterAuthenticator) -> WalterDB:
    return WalterDB(
        ddb=WalterDDBClient(ddb_client),
        authenticator=walter_authenticator,
        domain=Domain.TESTING,
    )


@pytest.fixture
def walter_cw(
    cloud_watch_client: CloudWatchClient,
) -> WalterCloudWatchClient:
    return WalterCloudWatchClient(client=cloud_watch_client, domain=Domain.TESTING)


@pytest.fixture
def templates_bucket(walter_s3: WalterS3Client) -> TemplatesBucket:
    return TemplatesBucket(client=walter_s3, domain=Domain.TESTING)


@pytest.fixture
def template_engine(templates_bucket: TemplatesBucket) -> None:
    return TemplatesEngine(templates_bucket)


@pytest.fixture
def newsletters_queue(sqs_client) -> NewslettersQueue:
    return NewslettersQueue(
        client=WalterSQSClient(client=sqs_client, domain=Domain.TESTING)
    )


@pytest.fixture
def jwt_walter(walter_authenticator: WalterAuthenticator) -> str:
    return walter_authenticator.generate_user_token("walter@gmail.com")


@pytest.fixture
def jwt_walrus(walter_authenticator: WalterAuthenticator) -> str:
    return walter_authenticator.generate_user_token("walrus@gmail.com")
