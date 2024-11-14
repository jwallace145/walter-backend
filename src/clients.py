import os

import boto3

from src.ai.client import WalterAI
from src.ai.context.generator import ContextGenerator
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
from src.newsletters.client import NewslettersBucket
from src.newsletters.queue import NewslettersQueue
from src.stocks.client import WalterStocksAPI
from src.stocks.polygon.client import PolygonClient
from src.templates.bucket import TemplatesBucket
from src.templates.engine import TemplatesEngine
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

##############
# S3 BUCKETS #
##############

s3 = WalterS3Client(client=boto3.client("s3", region_name=AWS_REGION), domain=DOMAIN)
templates_bucket = TemplatesBucket(s3, DOMAIN)
newsletters_bucket = NewslettersBucket(s3, DOMAIN)

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

walter_authenticator = WalterAuthenticator(jwt_secret_key=JWT_TOKEN_KEY)

#####################
# NEWSLETTERS QUEUE #
#####################

newsletters_queue = NewslettersQueue(
    client=WalterSQSClient(
        client=boto3.client("sqs", region_name=AWS_REGION), domain=DOMAIN
    )
)

##########################
# WALTER DATABASE CLIENT #
##########################

walter_db = WalterDB(
    ddb=WalterDDBClient(client=boto3.client("dynamodb", region_name=AWS_REGION)),
    authenticator=walter_authenticator,
    domain=DOMAIN,
)

#####################
# WALTER STOCKS API #
#####################

walter_stocks_api = WalterStocksAPI(
    client=PolygonClient(
        api_key=POLYGON_API_KEY,
    )
)


#########################
# JINJA TEMPLATE ENGINE #
#########################

template_engine = TemplatesEngine(templates_bucket=templates_bucket)

#############
# WALTER AI #
#############

walter_ai = WalterAI(
    model=CONFIG.model_id,
    client=WalterBedrockClient(
        bedrock=boto3.client("bedrock", region_name=AWS_REGION),
        bedrock_runtime=boto3.client("bedrock-runtime", region_name=AWS_REGION),
    ),
)

#####################
# CONTEXT GENERATOR #
#####################

context_generator = ContextGenerator()
