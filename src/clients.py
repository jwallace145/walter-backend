import os

import boto3

from plaid import Environment
from src.ai.mlp.expenses import ExpenseCategorizerMLP
from src.auth.authenticator import WalterAuthenticator
from src.aws.dynamodb.client import WalterDDBClient
from src.aws.s3.client import WalterS3Client
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.aws.sqs.client import WalterSQSClient
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

log = Logger(__name__).get_logger()

log.debug("Initializing clients...")

#########################
# ENVIRONMENT VARIABLES #
#########################

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
"""(str): The AWS region the WalterBackend service is deployed."""

DOMAIN = Domain.from_string(os.getenv("DOMAIN", "dev"))
"""(str): The domain of the WalterBackend service environment."""


###########
# METRICS #
###########

log.debug("Creating Datadog metrics client...")

DATADOG = DatadogMetricsClient(domain=DOMAIN)
"""(DatadogMetricsClient): The Datadog metrics client used to emit metrics to Datadog."""

#################
# BOTO3 CLIENTS #
#################

log.debug("Creating Boto3 clients...")

S3 = WalterS3Client(client=boto3.client("s3", region_name=AWS_REGION), domain=DOMAIN)
"""(WalterS3Client): The S3 client used to interact with the WalterBackend S3 buckets."""

DYNAMODB = WalterDDBClient(client=boto3.client("dynamodb", region_name=AWS_REGION))
"""(WalterDDBClient): The DynamoDB client used to interact with the WalterBackend database."""

SECRETS = WalterSecretsManagerClient(
    client=boto3.client("secretsmanager", region_name=AWS_REGION), domain=DOMAIN
)
"""(WalterSecretsManagerClient): The Secrets Manager client used to interact with the WalterBackend secrets."""

SQS = WalterSQSClient(client=boto3.client("sqs", region_name=AWS_REGION), domain=DOMAIN)
"""(WalterSQSClient): The SQS client used to interact with the WalterBackend SQS queues."""


#################
# AUTHENTICATOR #
#################

log.debug("Creating authenticator client...")

AUTHENTICATOR = WalterAuthenticator(SECRETS)
"""(WalterAuthenticator): The Walter Authenticator client used to authenticate users."""


############
# DATABASE #
############

log.debug("Creating database client...")

DATABASE = WalterDB(
    ddb=DYNAMODB,
    authenticator=AUTHENTICATOR,
    domain=DOMAIN,
)
"""(WalterDB): The Walter Database client used to interact with all tables included in the DynamoDB database."""

HOLDING_UPDATER = HoldingUpdater(DATABASE)
"""(HoldingUpdater): The Walter Holding Updater client used to update holdings in the DynamoDB database."""


######################
# POLYGON & SECURITY #
######################

POLYGON = PolygonClient(SECRETS)
"""(PolygonClient): The client used to interact with the Polygon API and get the latest pricing data."""

SECURITY_UPDATER = SecurityUpdater(POLYGON, DATABASE)
"""(SecurityUpdater): The client used to update new security prices in the DynamoDB database."""


EXPENSE_CATEGORIZER = ExpenseCategorizerMLP()
"""(ExpenseCategorizerMLP): The client used to categorize user expenses."""


#########
# PLAID #
#########

TXN_CONVERTER = TransactionConverter(DATABASE)
"""(TransactionConverter): The client used to convert Plaid transactions to WalterDB transactions."""

PLAID = PlaidClient(SECRETS, DATABASE, Environment.Sandbox, TXN_CONVERTER)
"""(PlaidClient): The client used to interact with the Plaid API."""

SYNC_TRANSACTIONS_QUEUE = SyncUserTransactionsTaskQueue(SQS)
"""(SyncUserTransactionsTaskQueue): The client used to interact with the Plaid API."""
