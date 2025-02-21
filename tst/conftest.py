import json
import os
from datetime import datetime as dt

import boto3
import pytest
from moto import mock_aws
from mypy_boto3_cloudwatch import CloudWatchClient
from mypy_boto3_dynamodb import DynamoDBClient
from mypy_boto3_s3.client import S3Client
from mypy_boto3_secretsmanager import SecretsManagerClient
from mypy_boto3_ses.client import SESClient
from mypy_boto3_sqs import SQSClient

from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.dynamodb.client import WalterDDBClient
from src.aws.s3.client import WalterS3Client
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.aws.ses.client import WalterSESClient
from src.aws.sqs.client import WalterSQSClient
from src.database.client import WalterDB
from src.environment import Domain
from src.events.parser import WalterEventParser
from src.news.bucket import NewsSummariesBucket
from src.news.queue import NewsSummariesQueue
from src.newsletters.client import NewslettersBucket
from src.newsletters.queue import NewslettersQueue
from src.stocks.client import WalterStocksAPI
from src.stocks.polygon.client import PolygonClient
from src.templates.bucket import TemplatesBucket
from src.templates.engine import TemplatesEngine
from tst.constants import (
    AWS_REGION,
    SECRETS_MANAGER_POLYGON_API_KEY_NAME,
    SECRETS_MANAGER_POLYGON_API_KEY_VALUE,
    SECRETS_MANAGER_JWT_SECRET_KEY_SECRET_NAME,
    SECRETS_MANAGER_JWT_SECRET_KEY_SECRET_VALUE,
    SECRETS_MANAGER_CHANGE_PASSWORD_KEY_SECRET_NAME,
    SECRETS_MANAGER_CHANGE_PASSWORD_KEY_SECRET_VALUE,
    SECRETS_MANAGER_VERIFY_EMAIL_KEY_SECRET_NAME,
    SECRETS_MANAGER_VERIFY_EMAIL_KEY_SECRET_VALUE,
    NEWS_SUMMARIES_QUEUE_NAME,
    NEWSLETTERS_QUEUE_NAME,
)
from tst.database.mock import MockDDB
from tst.stocks.mock import MockPolygon, MockAlphaVantageClient


###################
# GLOBAL FIXTURES #
###################


@pytest.fixture
def ddb_client() -> DynamoDBClient:
    with mock_aws():
        mock_ddb = boto3.client("dynamodb", region_name=AWS_REGION)
        MockDDB(mock_ddb).initialize()
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
        mock_secrets_manager.create_secret(
            Name=SECRETS_MANAGER_VERIFY_EMAIL_KEY_SECRET_NAME,
            SecretString=json.dumps(
                {
                    "JWTVerifyEmailSecretKey": SECRETS_MANAGER_VERIFY_EMAIL_KEY_SECRET_VALUE
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
        mock_sqs.create_queue(QueueName=NEWS_SUMMARIES_QUEUE_NAME)
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
        mock_s3.create_bucket(Bucket="walterai-newsletters-unittest")
        mock_s3.create_bucket(Bucket="walterai-news-summaries-unittest")
        now = dt.now()
        mock_s3.put_object(
            Bucket="walterai-news-summaries-unittest",
            Key=f"summaries/MSFT/{now.strftime('y=%Y/m=%m/d=%d')}/metadata.json",
            Body=json.dumps(
                {
                    "stock": "MSFT",
                    "company": "Microsoft",
                    "datestamp": now.strftime("%Y-%m-%d"),
                    "model_name": "Test Model",
                }
            ),
        )
        mock_s3.put_object(
            Bucket="walterai-news-summaries-unittest",
            Key=f"summaries/MSFT/{now.strftime('y=%Y/m=%m/d=%d')}/summary.html",
            Body="news summary",
        )
        mock_s3.put_object(
            Bucket="walterai-news-summaries-unittest",
            Key=f"summaries/AAPL/{now.strftime('y=%Y/m=%m/d=%d')}/metadata.json",
            Body=json.dumps(
                {
                    "stock": "AAPL",
                    "company": "Apple Inc",
                    "datestamp": now.strftime("%Y-%m-%d"),
                    "model_name": "Test Model",
                }
            ),
        )
        mock_s3.put_object(
            Bucket="walterai-news-summaries-unittest",
            Key=f"summaries/AAPL/{now.strftime('y=%Y/m=%m/d=%d')}/summary.html",
            Body="apple news summary",
        )
        mock_s3.put_object(
            Bucket="walterai-news-summaries-unittest",
            Key=f"summaries/META/{now.strftime('y=%Y/m=%m/d=%d')}/metadata.json",
            Body=json.dumps(
                {
                    "stock": "META",
                    "company": "Meta Platforms Inc.",
                    "datestamp": now.strftime("%Y-%m-%d"),
                    "model_name": "Test Model",
                }
            ),
        )
        mock_s3.put_object(
            Bucket="walterai-news-summaries-unittest",
            Key=f"summaries/META/{now.strftime('y=%Y/m=%m/d=%d')}/summary.html",
            Body="meta news summary",
        )
        yield mock_s3


@pytest.fixture
def ses_client() -> SESClient:
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
    return WalterStocksAPI(
        polygon=PolygonClient(
            api_key=SECRETS_MANAGER_POLYGON_API_KEY_VALUE,
            client=MockPolygon(mocker).create_client(),
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
def newsletters_bucket(walter_s3: WalterS3Client) -> NewslettersBucket:
    return NewslettersBucket(client=walter_s3, domain=Domain.TESTING)


@pytest.fixture
def news_summaries_queue(sqs_client) -> NewsSummariesQueue:
    return NewsSummariesQueue(
        client=WalterSQSClient(client=sqs_client, domain=Domain.TESTING)
    )


@pytest.fixture
def news_summaries_bucket(walter_s3: WalterS3Client) -> NewsSummariesBucket:
    return NewsSummariesBucket(client=walter_s3, domain=Domain.TESTING)


@pytest.fixture
def jwt_walter(walter_authenticator: WalterAuthenticator) -> str:
    return walter_authenticator.generate_user_token("walter@gmail.com")


@pytest.fixture
def jwt_walrus(walter_authenticator: WalterAuthenticator) -> str:
    return walter_authenticator.generate_user_token("walrus@gmail.com")


@pytest.fixture
def jwt_bob(walter_authenticator: WalterAuthenticator) -> str:
    return walter_authenticator.generate_user_token("bob@gmail.com")


@pytest.fixture
def jwt_john(walter_authenticator: WalterAuthenticator) -> str:
    return walter_authenticator.generate_user_token("john@gmail.com")


@pytest.fixture
def walter_event_parser() -> WalterEventParser:
    return WalterEventParser()
