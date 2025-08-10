import os

import boto3
from plaid import Environment

from src.ai.client import WalterAI
from src.ai.mlp.expenses import ExpenseCategorizerMLP
from src.api.accounts.cash.create_cash_account import CreateCashAccount
from src.api.accounts.cash.delete_cash_account import DeleteCashAccount
from src.api.accounts.cash.get_cash_accounts import GetCashAccounts
from src.api.accounts.cash.update_cash_account import UpdateCashAccount
from src.api.accounts.credit.create_credit_account import CreateCreditAccount
from src.api.accounts.credit.delete_credit_account import DeleteCreditAccount
from src.api.accounts.credit.get_credit_accounts import GetCreditAccounts
from src.api.accounts.investments.create_investment_account import (
    CreateInvestmentAccount,
)
from src.api.accounts.investments.delete_investment_account import (
    DeleteInvestmentAccount,
)
from src.api.accounts.investments.get_investment_accounts import GetInvestmentAccounts
from src.api.add_stock import AddStock
from src.api.auth_user import AuthUser
from src.api.create_user import CreateUser
from src.api.delete_stock import DeleteStock
from src.api.get_portfolio import GetPortfolio
from src.api.get_prices import GetPrices
from src.api.get_stock import GetStock
from src.api.get_user import GetUser
from src.api.plaid.create_link_token import CreateLinkToken
from src.api.plaid.exchange_public_token import ExchangePublicToken
from src.api.plaid.refresh_transactions import RefreshTransactions
from src.api.plaid.sync_transactions import SyncTransactions
from src.api.transactions.add_transaction import AddTransaction
from src.api.transactions.delete_transaction import DeleteTransaction
from src.api.transactions.edit_transaction import EditTransaction
from src.api.transactions.get_transactions import GetTransactions
from src.api.update_user import UpdateUser
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
from src.news.bucket import NewsSummariesBucket
from src.news.queue import NewsSummariesQueue
from src.transactions.queue import SyncUserTransactionsQueue
from src.newsletters.client import NewslettersBucket
from src.newsletters.queue import NewslettersQueue
from src.payments.stripe.client import WalterStripeClient
from src.plaid.client import PlaidClient
from src.stocks.alphavantage.client import AlphaVantageClient
from src.stocks.client import WalterStocksAPI
from src.stocks.polygon.client import PolygonClient
from src.stocks.stocknews.client import StockNewsClient
from src.summaries.client import WalterNewsSummaryClient
from src.templates.bucket import TemplatesBucket
from src.templates.engine import TemplatesEngine
from src.utils.log import Logger
from src.utils.web_scraper import WebScraper

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
newsletters_bucket = NewslettersBucket(s3, DOMAIN)
news_summaries_bucket = NewsSummariesBucket(s3, DOMAIN)
templates_bucket = TemplatesBucket(s3, DOMAIN)

###########
# SECRETS #
###########

walter_sm = WalterSecretsManagerClient(
    client=boto3.client("secretsmanager", region_name=AWS_REGION), domain=DOMAIN
)

ALPHA_VANTAGE_API_KEY = walter_sm.get_alpha_vantage_api_key()
POLYGON_API_KEY = walter_sm.get_polygon_api_key()
STOCK_NEWS_API_KEY = walter_sm.get_stock_news_api_key()
JWT_TOKEN_KEY = walter_sm.get_jwt_secret_key()

########################
# WALTER AUTHENTICATOR #
########################

walter_authenticator = WalterAuthenticator(walter_sm=walter_sm)

#####################
# NEWSLETTERS QUEUE #
#####################

newsletters_queue = NewslettersQueue(client=walter_sqs)

########################
# NEWS SUMMARIES QUEUE #
########################

news_summaries_queue = NewsSummariesQueue(client=walter_sqs)

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

web_scraper = WebScraper()

walter_stocks_api = WalterStocksAPI(
    polygon=PolygonClient(
        api_key=POLYGON_API_KEY,
    ),
    alpha_vantage=AlphaVantageClient(
        api_key=ALPHA_VANTAGE_API_KEY, web_scraper=web_scraper
    ),
    stock_news=StockNewsClient(api_key=STOCK_NEWS_API_KEY, web_scraper=web_scraper),
)

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

##############################
# WALTER NEWS SUMMARY CLIENT #
##############################

walter_news_summary_client = WalterNewsSummaryClient(
    walter_stock_api=walter_stocks_api, walter_ai=walter_ai, walter_cw=walter_cw
)

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

# CASH ACCOUNTS
get_cash_accounts_api = GetCashAccounts(walter_authenticator, walter_cw, walter_db)
create_cash_account_api = CreateCashAccount(walter_authenticator, walter_cw, walter_db)
update_cash_account_api = UpdateCashAccount(walter_authenticator, walter_cw, walter_db)
delete_cash_account_api = DeleteCashAccount(walter_authenticator, walter_cw, walter_db)

# CREDIT ACCOUNTS
get_credit_accounts_api = GetCreditAccounts(walter_authenticator, walter_cw, walter_db)
create_credit_account_api = CreateCreditAccount(
    walter_authenticator, walter_cw, walter_db
)
delete_credit_account_api = DeleteCreditAccount(
    walter_authenticator, walter_cw, walter_db
)

# INVESTMENT ACCOUNTS
create_investment_account_api = CreateInvestmentAccount(
    walter_authenticator, walter_cw, walter_db
)
get_investment_accounts_api = GetInvestmentAccounts(
    walter_authenticator, walter_cw, walter_db
)
delete_investment_account_api = DeleteInvestmentAccount(
    walter_authenticator, walter_cw, walter_db
)

# PORTFOLIOS
get_portfolio_api = GetPortfolio(
    walter_authenticator, walter_cw, walter_db, walter_sm, walter_stocks_api
)

# PRICES
get_prices_api = GetPrices(
    walter_authenticator, walter_cw, walter_db, walter_stocks_api
)

# STOCKS
get_stocks_api = GetStock(walter_authenticator, walter_cw, walter_db, walter_stocks_api)
add_stock_api = AddStock(
    walter_authenticator, walter_cw, walter_db, walter_stocks_api, walter_sm
)
delete_stock_api = DeleteStock(
    walter_authenticator, walter_cw, walter_db, walter_stocks_api, walter_sm
)

# TRANSACTIONS
get_transactions_api = GetTransactions(walter_authenticator, walter_cw, walter_db)
add_transaction_api = AddTransaction(
    walter_authenticator, walter_cw, walter_db, expense_categorizer
)
edit_transaction_api = EditTransaction(walter_authenticator, walter_cw, walter_db)
delete_transaction_api = DeleteTransaction(walter_authenticator, walter_cw, walter_db)

# USERS
get_user_api = GetUser(walter_authenticator, walter_cw, walter_db, walter_sm, s3)
create_user_api = CreateUser(
    walter_authenticator,
    walter_cw,
    walter_db,
    walter_ses,
    template_engine,
    templates_bucket,
)
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
