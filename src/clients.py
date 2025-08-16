import os

import boto3

from plaid import Environment
from src.ai.client import WalterAI
from src.ai.mlp.expenses import ExpenseCategorizerMLP
from src.api.accounts.create_account import CreateAccount
from src.api.accounts.delete_account import DeleteAccount
from src.api.accounts.get_accounts import GetAccounts
from src.api.accounts.update_account import UpdateAccount
from src.api.auth.auth_user import AuthUser
from src.api.plaid.create_link_token import CreateLinkToken
from src.api.plaid.exchange_public_token import ExchangePublicToken
from src.api.plaid.refresh_transactions import RefreshTransactions
from src.api.plaid.sync_transactions import SyncTransactions
from src.api.transactions.add_transaction import AddTransaction
from src.api.transactions.delete_transaction import DeleteTransaction
from src.api.transactions.edit_transaction import EditTransaction
from src.api.transactions.get_transactions import GetTransactions
from src.api.users.create_user import CreateUser
from src.api.users.get_user import GetUser
from src.api.users.update_user import UpdateUser
from src.auth.authenticator import WalterAuthenticator
from src.aws.bedrock.client import WalterBedrockClient
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.dynamodb.client import WalterDDBClient
from src.aws.s3.client import WalterS3Client
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.aws.ses.client import WalterSESClient
from src.aws.sqs.client import WalterSQSClient
from src.config import CONFIG
from src.database.client import WalterDB
from src.environment import get_domain
from src.events.parser import WalterEventParser
from src.media.bucket import PublicMediaBucket
from src.payments.stripe.client import WalterStripeClient
from src.plaid.client import PlaidClient
from src.polygon.client import PolygonClient
from src.templates.bucket import TemplatesBucket
from src.templates.engine import TemplatesEngine
from src.transactions.queue import SyncUserTransactionsQueue
from src.utils.log import Logger

log = Logger(__name__).get_logger()

log.debug("Initializing clients...")

#########################
# ENVIRONMENT VARIABLES #
#########################

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
"""(str): The AWS region the WalterBackend service is deployed."""

DOMAIN = get_domain(os.getenv("DOMAIN", "DEVELOPMENT"))
"""(str): The domain of the WalterBackend service environment."""

#######################
# WALTER EVENT PARSER #
#######################

walter_event_parser = WalterEventParser()


########################
# WALTER BOTO3 CLIENTS #
########################

walter_cw = WalterCloudWatchClient(
    client=boto3.client("cloudwatch", region_name=AWS_REGION), domain=DOMAIN
)
walter_ses = WalterSESClient(
    client=boto3.client("ses", region_name=AWS_REGION), domain=DOMAIN
)
walter_sqs = WalterSQSClient(
    client=boto3.client("sqs", region_name=AWS_REGION), domain=DOMAIN
)

###########
# BUCKETS #
###########

s3 = WalterS3Client(client=boto3.client("s3", region_name=AWS_REGION), domain=DOMAIN)

public_media_bucket = PublicMediaBucket(s3, DOMAIN)
templates_bucket = TemplatesBucket(s3, DOMAIN)

###########
# SECRETS #
###########

walter_sm = WalterSecretsManagerClient(
    client=boto3.client("secretsmanager", region_name=AWS_REGION), domain=DOMAIN
)

POLYGON_API_KEY = walter_sm.get_polygon_api_key()
JWT_TOKEN_KEY = walter_sm.get_jwt_secret_key()

########################
# WALTER AUTHENTICATOR #
########################

walter_authenticator = WalterAuthenticator(walter_sm=walter_sm)

#############
# WALTER DB #
#############

walter_db = WalterDB(
    ddb=WalterDDBClient(client=boto3.client("dynamodb", region_name=AWS_REGION)),
    authenticator=walter_authenticator,
    domain=DOMAIN,
)

#####################
# WALTER STOCKS API #
#####################

polygon_client = PolygonClient(api_key=POLYGON_API_KEY)

#########################
# JINJA TEMPLATE ENGINE #
#########################

template_engine = TemplatesEngine(templates_bucket=templates_bucket)

#############
# WALTER AI #
#############

walter_ai = WalterAI(
    model_name=CONFIG.artificial_intelligence.model_name,
    client=WalterBedrockClient(
        bedrock=boto3.client("bedrock", region_name=AWS_REGION),
        bedrock_runtime=boto3.client("bedrock-runtime", region_name=AWS_REGION),
    ),
)

expense_categorizer = ExpenseCategorizerMLP()

###################
# WALTER PAYMENTS #
###################

walter_payments = WalterStripeClient(walter_sm=walter_sm)


#########
# PLAID #
#########

plaid = PlaidClient(
    client_id=walter_sm.get_plaid_sandbox_credentials_client_id(),
    secret=walter_sm.get_plaid_sandbox_credentials_secret_key(),
    environment=Environment.Sandbox,
)

sync_user_transactions_queue = SyncUserTransactionsQueue(client=walter_sqs)

###############
# API METHODS #
###############

# AUTHENTICATION
auth_user_api = AuthUser(walter_authenticator, walter_cw, walter_db, walter_sm)

# ACCOUNTS =
get_accounts_api = GetAccounts(walter_authenticator, walter_cw, walter_db)
create_account_api = CreateAccount(walter_authenticator, walter_cw, walter_db)
update_account_api = UpdateAccount(walter_authenticator, walter_cw, walter_db)
delete_account_api = DeleteAccount(walter_authenticator, walter_cw, walter_db)


# TRANSACTIONS
get_transactions_api = GetTransactions(walter_authenticator, walter_cw, walter_db)
add_transaction_api = AddTransaction(
    walter_authenticator, walter_cw, walter_db, expense_categorizer, polygon_client
)
edit_transaction_api = EditTransaction(walter_authenticator, walter_cw, walter_db)
delete_transaction_api = DeleteTransaction(walter_authenticator, walter_cw, walter_db)

# USERS
get_user_api = GetUser(walter_authenticator, walter_cw, walter_db, walter_sm, s3)
create_user_api = CreateUser(walter_authenticator, walter_cw, walter_db)
update_user_api = UpdateUser(walter_authenticator, walter_cw, walter_db, s3)

# PLAID
plaid_create_link_token_api = CreateLinkToken(
    walter_authenticator, walter_cw, walter_db, plaid
)
plaid_exchange_public_token_api = ExchangePublicToken(
    walter_authenticator,
    walter_cw,
    walter_db,
    plaid,
    sync_user_transactions_queue,
)
plaid_sync_transactions_api = SyncTransactions(
    walter_authenticator,
    walter_cw,
    walter_db,
    sync_user_transactions_queue,
)
plaid_refresh_transactions_api = RefreshTransactions(
    walter_authenticator, walter_cw, walter_db, plaid
)
