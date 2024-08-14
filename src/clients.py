import os

import boto3
from src.bedrock.client import BedrockClient
from src.cloudwatch.client import CloudWatchClient
from src.dynamodb.client import DDBClient
from src.environment import get_domain
from src.jinja.client import TemplateEngine
from src.polygon.client import PolygonClient
from src.report.generator import ReportGenerator
from src.s3.client import WalterS3Client
from src.s3.newsletters.client import NewslettersBucket
from src.s3.templates.client import TemplatesBucket
from src.secretsmanager.client import SecretsManagerClient
from src.ses.client import SESClient
from src.utils.log import Logger

log = Logger(__name__).get_logger()

#########################
# ENVIRONMENT VARIABLES #
#########################

AWS_REGION = os.getenv("AWS_REGION")
"""(str): The AWS region the WalterAIBackend service is deployed."""

DOMAIN = get_domain(os.getenv("DOMAIN"))
"""(str): The domain of the WalterAIBackend service environment."""

########################
# WALTER BOTO3 CLIENTS #
########################

bedrock = BedrockClient(
    bedrock=boto3.client("bedrock", region_name=AWS_REGION),
    bedrock_runtime=boto3.client("bedrock-runtime", region_name=AWS_REGION),
)
cloudwatch = CloudWatchClient(
    client=boto3.client("cloudwatch", region_name=AWS_REGION), domain=DOMAIN
)
ddb = DDBClient(client=boto3.client("dynamodb", region_name=AWS_REGION), domain=DOMAIN)
secretsmanager = SecretsManagerClient(
    client=boto3.client("secretsmanager", region_name=AWS_REGION), domain=DOMAIN
)
ses = SESClient(client=boto3.client("ses", region_name=AWS_REGION), domain=DOMAIN)

##############
# S3 BUCKETS #
##############

s3 = WalterS3Client(client=boto3.client("s3", region_name=AWS_REGION), domain=DOMAIN)
templates_bucket = TemplatesBucket(s3, DOMAIN)
newsletters_bucket = NewslettersBucket(s3, DOMAIN)

#########################
# JINJA TEMPLATE ENGINE #
#########################

template_engine = TemplateEngine(
    templates_bucket=templates_bucket,
    newsletters_bucket=newsletters_bucket,
    domain=DOMAIN,
)

##################
# POLYGON CLIENT #
##################

polygon = PolygonClient(api_key=secretsmanager.polygon_api_key)

####################
# REPORT GENERATOR #
####################

report_generator = ReportGenerator()
