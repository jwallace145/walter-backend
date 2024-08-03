import os

import boto3
from src.bedrock.client import BedrockClient
from src.dynamodb.client import DDBClient
from src.environment import get_domain
from src.polygon.client import PolygonClient
from src.s3.client import S3Client
from src.ses.client import SESClient
from src.utils.log import Logger
from src.report.generator import ReportGenerator
from src.secretsmanager.client import SecretsManagerClient

log = Logger(__name__).get_logger()

API_KEY = os.getenv("POLYGON_API_KEY")
AWS_REGION = os.getenv("AWS_REGION")
DOMAIN = get_domain(os.getenv("DOMAIN"))

log.info("Creating WalterAI clients")
secretsmanager = SecretsManagerClient(
    client=boto3.client("secretsmanager", region_name=AWS_REGION), domain=DOMAIN
)
bedrock = BedrockClient(
    bedrock=boto3.client("bedrock", region_name=AWS_REGION),
    bedrock_runtime=boto3.client("bedrock-runtime", region_name=AWS_REGION),
)
ddb = DDBClient(client=boto3.client("dynamodb", region_name=AWS_REGION), domain=DOMAIN)
s3 = S3Client(client=boto3.client("s3", region_name=AWS_REGION), domain=DOMAIN)
ses = SESClient(client=boto3.client("ses", region_name=AWS_REGION), domain=DOMAIN)
polygon = PolygonClient(api_key=secretsmanager.polygon_api_key)
report_generator = ReportGenerator()
