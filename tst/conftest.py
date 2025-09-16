import boto3
import pytest
from moto import mock_aws
from mypy_boto3_dynamodb import DynamoDBClient
from mypy_boto3_s3.client import S3Client
from mypy_boto3_secretsmanager import SecretsManagerClient
from mypy_boto3_ses.client import SESClient
from mypy_boto3_sqs import SQSClient

from src.ai.mlp.expenses import ExpenseCategorizerMLP
from src.api.factory import APIMethodFactory
from src.auth.authenticator import WalterAuthenticator
from src.aws.dynamodb.client import WalterDDBClient
from src.aws.s3.client import WalterS3Client
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.aws.ses.client import WalterSESClient
from src.aws.sqs.client import WalterSQSClient
from src.canaries.routing.router import CanaryRouter
from src.database.client import WalterDB
from src.environment import Domain
from src.factory import ClientFactory
from src.investments.holdings.updater import HoldingUpdater
from src.investments.securities.updater import SecurityUpdater
from src.metrics.client import DatadogMetricsClient
from src.transactions.queue import SyncUserTransactionsTaskQueue
from src.workflows.factory import WorkflowFactory
from tst.aws.mock import MockS3, MockSecretsManager, MockSQS
from tst.constants import AWS_REGION
from tst.database.mock import MockDDB
from tst.plaid.mock import MockPlaidClient
from tst.polygon.mock import MockPolygonClient
from tst.transactions.mock import MockTransactionsCategorizer

######################
# BOTO3 CLIENT MOCKS #
######################


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
        MockSecretsManager(mock_secrets_manager).initialize()
        yield mock_secrets_manager


@pytest.fixture
def sqs_client() -> SQSClient:
    with mock_aws():
        mock_sqs = boto3.client("sqs", region_name=AWS_REGION)
        MockSQS(mock_sqs).initialize()
        yield mock_sqs


@pytest.fixture
def s3_client() -> S3Client:
    with mock_aws():
        mock_s3 = boto3.client("s3", region_name=AWS_REGION)
        MockS3(mock_s3).initialize()
        yield mock_s3


@pytest.fixture
def ses_client() -> SESClient:
    with mock_aws():
        mock_ses = boto3.client("ses", region_name=AWS_REGION)
        yield mock_ses


#################################
# WALTER BACKEND BOTO3 WRAPPERS #
#################################


@pytest.fixture
def walter_sm(
    secrets_manager_client: SecretsManagerClient,
) -> WalterSecretsManagerClient:
    return WalterSecretsManagerClient(
        client=secrets_manager_client, domain=Domain.TESTING
    )


@pytest.fixture
def walter_db(ddb_client, walter_authenticator: WalterAuthenticator) -> WalterDB:
    return WalterDB(
        ddb=WalterDDBClient(ddb_client),
        authenticator=walter_authenticator,
        domain=Domain.TESTING,
    )


@pytest.fixture
def walter_s3(s3_client: S3Client) -> WalterS3Client:
    return WalterS3Client(client=s3_client, domain=Domain.TESTING)


@pytest.fixture
def walter_ses(ses_client: SESClient) -> WalterSESClient:
    return WalterSESClient(client=ses_client, domain=Domain.TESTING)


@pytest.fixture
def walter_sqs(sqs_client: SQSClient) -> WalterSQSClient:
    return WalterSQSClient(client=sqs_client, domain=Domain.TESTING)


##################
# AUTHENTICATION #
##################


@pytest.fixture
def walter_authenticator(walter_sm: WalterSecretsManagerClient) -> WalterAuthenticator:
    return WalterAuthenticator(walter_sm=walter_sm)


#######################
# MOCK POLYGON CLIENT #
#######################


@pytest.fixture
def polygon_client() -> MockPolygonClient:
    return MockPolygonClient()


#####################
# MOCK PLAID CLIENT #
#####################


@pytest.fixture
def plaid_client() -> MockPlaidClient:
    return MockPlaidClient()


################
# MOCK METRICS #
################


@pytest.fixture
def datadog_metrics() -> DatadogMetricsClient:
    # Lightweight mock of DatadogMetricsClient that swallows metric emissions
    class MockDatadogMetrics(DatadogMetricsClient):
        def __init__(self):
            super().__init__(domain=Domain.TESTING)
            self.emitted = []

        def emit_metric(self, metric_name, metric_value, tags=None):
            # record but do not emit externally
            self.emitted.append((metric_name, metric_value, tags))

    return MockDatadogMetrics()


@pytest.fixture
def sync_transactions_task_queue(
    walter_sqs: WalterSQSClient,
) -> SyncUserTransactionsTaskQueue:
    return SyncUserTransactionsTaskQueue(walter_sqs)


@pytest.fixture
def transactions_categorizer() -> ExpenseCategorizerMLP:
    return MockTransactionsCategorizer()


@pytest.fixture
def holding_updater(walter_db: WalterDB) -> HoldingUpdater:
    return HoldingUpdater(walter_db)


@pytest.fixture
def security_updater(
    polygon_client: MockPolygonClient, walter_db: WalterDB
) -> SecurityUpdater:
    return SecurityUpdater(polygon_client, walter_db)


############################
# UNIT TEST CLIENT FACTORY #
############################


@pytest.fixture
def client_factory(
    datadog_metrics: DatadogMetricsClient,
    walter_s3: WalterS3Client,
    ddb_client: DynamoDBClient,
    walter_db: WalterDB,
    walter_sm: WalterSecretsManagerClient,
    walter_sqs: WalterSQSClient,
    walter_authenticator: WalterAuthenticator,
    polygon_client: MockPolygonClient,
    security_updater: SecurityUpdater,
    holding_updater: HoldingUpdater,
    transactions_categorizer: MockTransactionsCategorizer,
    plaid_client: MockPlaidClient,
    sync_transactions_task_queue: SyncUserTransactionsTaskQueue,
) -> ClientFactory:
    # create a client factory
    client_factory: ClientFactory = ClientFactory(
        domain=Domain.TESTING, region=AWS_REGION
    )

    # set factory clients to mocked clients for unit tests
    client_factory.metrics = datadog_metrics
    client_factory.s3 = walter_s3
    client_factory.ddb = ddb_client
    client_factory.secrets = walter_sm
    client_factory.sqs = walter_sqs
    client_factory.sts = None  # TODO: Support mock STS client creation for unit tests
    client_factory.auth = walter_authenticator
    client_factory.db = walter_db
    client_factory.polygon = polygon_client
    client_factory.security_updater = security_updater
    client_factory.holding_updater = holding_updater
    client_factory.expense_categorizer = transactions_categorizer
    client_factory.plaid = plaid_client
    client_factory.sync_transactions_task_queue = sync_transactions_task_queue

    # return the client factory configured with mock clients
    return client_factory


@pytest.fixture
def api_method_factory(client_factory: ClientFactory) -> APIMethodFactory:
    return APIMethodFactory(client_factory=client_factory)


@pytest.fixture
def workflow_factory(client_factory: ClientFactory) -> WorkflowFactory:
    return WorkflowFactory(client_factory=client_factory)


@pytest.fixture
def canary_router(client_factory: ClientFactory) -> CanaryRouter:
    return CanaryRouter(client_factory=client_factory)
