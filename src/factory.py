from dataclasses import dataclass

import boto3

from plaid import Environment
from src.ai.mlp.expenses import ExpenseCategorizerMLP
from src.auth.authenticator import WalterAuthenticator
from src.aws.dynamodb.client import WalterDDBClient
from src.aws.s3.client import WalterS3Client
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.aws.sqs.client import WalterSQSClient
from src.aws.sts.client import WalterSTSClient
from src.database.client import WalterDB
from src.environment import Domain
from src.investments.holdings.updater import HoldingUpdater
from src.investments.securities.updater import SecurityUpdater
from src.metrics.client import DatadogMetricsClient
from src.plaid.client import PlaidClient
from src.plaid.transaction_converter import TransactionConverter
from src.polygon.client import PolygonClient
from src.transactions.queue import SyncUserTransactionsTaskQueue
from src.utils.log import Logger

LOG = Logger(__name__).get_logger()


@dataclass(kw_only=True)
class ClientFactory:
    """Factory for WalterBackend clients"""

    region: str
    domain: Domain

    # AWS credentials are lazily set when needed
    aws_access_key_id: str = None
    aws_secret_access_key: str = None
    aws_session_token: str = None

    # all clients are lazily loaded
    metrics: DatadogMetricsClient = None
    s3: WalterS3Client = None
    ddb: WalterDDBClient = None
    secrets: WalterSecretsManagerClient = None
    sqs: WalterSQSClient = None
    sts: WalterSTSClient = None
    auth: WalterAuthenticator = None
    db: WalterDB = None
    polygon: PolygonClient = None
    security_updater: SecurityUpdater = None
    expense_categorizer: ExpenseCategorizerMLP = None
    holding_updater: HoldingUpdater = None
    transaction_converter: TransactionConverter = None
    plaid: PlaidClient = None
    sync_transactions_task_queue: SyncUserTransactionsTaskQueue = None

    def __post_init__(self) -> None:
        LOG.debug("Creating WalterBackend client factory")

    def set_aws_credentials(
        self, aws_access_key_id: str, aws_secret_access_key: str, aws_session_token: str
    ) -> None:
        LOG.info("Setting AWS credentials for Boto3 clients")
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_session_token = aws_session_token
        credentials_role_arn: str = WalterSTSClient(
            region=self.region,
            client=boto3.client(
                "sts",
                region_name=self.region,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                aws_session_token=self.aws_session_token,
            ),
            domain=self.domain,
        ).get_caller_identity()
        principal = "/".join(credentials_role_arn.split("/")[1:])
        LOG.info(f"Set AWS credentials to principal '{principal}'")

    def get_aws_region(self) -> str:
        return self.region

    def get_domain(self) -> Domain:
        return self.domain

    def get_metrics_client(self) -> DatadogMetricsClient:
        if self.metrics is None:
            self.metrics = DatadogMetricsClient(self.domain)
        return self.metrics

    def get_s3_client(self) -> WalterS3Client:
        if self.s3 is None:
            self.s3 = WalterS3Client(
                client=boto3.client(
                    "s3",
                    **self._boto3_client_kwargs(),
                ),
                domain=self.domain,
            )
        return self.s3

    def get_ddb_client(self) -> WalterDDBClient:
        if self.ddb is None:
            self.ddb = WalterDDBClient(
                client=boto3.client(
                    "dynamodb",
                    **self._boto3_client_kwargs(),
                )
            )
        return self.ddb

    def get_secrets_client(self) -> WalterSecretsManagerClient:
        if self.secrets is None:
            self.secrets = WalterSecretsManagerClient(
                client=boto3.client(
                    "secretsmanager",
                    **self._boto3_client_kwargs(),
                ),
                domain=self.domain,
            )
        return self.secrets

    def get_sqs_client(self) -> WalterSQSClient:
        if self.sqs is None:
            self.sqs = WalterSQSClient(
                client=boto3.client(
                    "sqs",
                    **self._boto3_client_kwargs(),
                ),
                domain=self.domain,
            )
        return self.sqs

    def get_sts_client(self) -> WalterSTSClient:
        """
        Create a WalterSTSClient instance using the current AWS credentials.

        This method creates a WalterSTSClient given the Lambda role credentials.
        This method purposefully uses the Boto3 default credentials provider chain
        to ensure that the Lambda's role credentials are used. The other Boto3 clients
        created by the factory will use the credentials provided by an STS AssumeRole
        API call using this client. This client should not be created with non-Lambda
        role credentials.

        Returns:
            (WalterSTSClient): The WalterSTSClient instance.
        """
        if self.sts is None:
            LOG.info("Creating STS client to assume roles")
            session = boto3.Session()
            creds = session.get_credentials()
            self.sts = WalterSTSClient(
                region=self.region,
                client=boto3.client(
                    "sts",
                    region_name=self.region,
                    aws_access_key_id=creds.access_key,
                    aws_secret_access_key=creds.secret_key,
                    aws_session_token=creds.token,
                ),
                domain=self.domain,
            )
            role_arn: str = self.sts.get_caller_identity()
            principal = role_arn.split(":")[5].split("/")[1]
            LOG.info(f"Created STS client with credentials for principal '{principal}'")
        return self.sts

    def get_authenticator(self) -> WalterAuthenticator:
        if self.auth is None:
            self.auth = WalterAuthenticator(self.get_secrets_client())
        return self.auth

    def get_db_client(self) -> WalterDB:
        if self.db is None:
            self.db = WalterDB(
                self.get_ddb_client(), self.get_authenticator(), self.domain
            )
        return self.db

    def get_polygon_client(self) -> PolygonClient:
        if self.polygon is None:
            self.polygon = PolygonClient(self.get_secrets_client())
        return self.polygon

    def get_transaction_converter(self) -> TransactionConverter:
        if self.transaction_converter is None:
            self.transaction_converter = TransactionConverter(
                self.get_db_client(), self.get_expense_categorizer()
            )
        return self.transaction_converter

    def get_expense_categorizer(self) -> ExpenseCategorizerMLP:
        if self.expense_categorizer is None:
            self.expense_categorizer = ExpenseCategorizerMLP()
        return self.expense_categorizer

    def get_holding_updater(self) -> HoldingUpdater:
        if self.holding_updater is None:
            self.holding_updater = HoldingUpdater(self.get_db_client())
        return self.holding_updater

    def get_security_updater(self) -> SecurityUpdater:
        if self.security_updater is None:
            self.security_updater = SecurityUpdater(self.get_db_client())
        return self.security_updater

    def get_plaid_client(self) -> PlaidClient:
        if self.plaid is None:
            self.plaid = PlaidClient(
                self.get_secrets_client(),
                self.get_db_client(),
                Environment.Sandbox,
                self.get_transaction_converter(),
            )
        return self.plaid

    def get_sync_transactions_task_queue(self) -> SyncUserTransactionsTaskQueue:
        if self.sync_transactions_task_queue is None:
            self.sync_transactions_task_queue = SyncUserTransactionsTaskQueue(
                self.get_sqs_client()
            )
        return self.sync_transactions_task_queue

    def _boto3_client_kwargs(self) -> dict:
        if (
            not self.aws_access_key_id
            or not self.aws_secret_access_key
            or not self.aws_session_token
        ):
            # if overrides are not provided, use the default credentials provider chain
            session = boto3.Session()
            creds = session.get_credentials()
            return dict(
                region_name=self.region,
                aws_access_key_id=creds.access_key,
                aws_secret_access_key=creds.secret_key,
                aws_session_token=creds.token,
            )
        return dict(
            region_name=self.region,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            aws_session_token=self.aws_session_token,
        )
