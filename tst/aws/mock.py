import json
from dataclasses import dataclass

from mypy_boto3_s3.client import S3Client
from mypy_boto3_secretsmanager.client import SecretsManagerClient
from mypy_boto3_sqs import SQSClient

from tst.constants import (
    NEWS_SUMMARIES_QUEUE_NAME,
    NEWSLETTERS_QUEUE_NAME,
    OBJECTS_TEST_FILE,
    SECRETS_TEST_FILE,
    TEMPLATES_BUCKET_NAME,
)


@dataclass
class MockSecretsManager:
    """
    MockSecretsManager
    """

    mock_secrets_manager: SecretsManagerClient

    def initialize(self) -> None:
        self._create_secrets()

    def _create_secrets(self) -> None:
        with open(SECRETS_TEST_FILE) as secrets_f:

            # create secrets collected by secret name
            secrets = {}
            for secret in secrets_f:
                if not secret.strip():
                    continue
                json_secret = json.loads(secret)
                name = json_secret["name"]
                key = json_secret["key"]
                value = json_secret["value"]
                if name in secrets:
                    secrets[name][key] = value
                else:
                    secrets[name] = {key: value}

            # insert secrets into mock secrets manager
            for secret_name, secrets_dict in secrets.items():
                self.mock_secrets_manager.create_secret(
                    Name=secret_name,
                    SecretString=json.dumps(secrets_dict),
                )


@dataclass
class MockS3:
    """
    MockS3
    """

    s3: S3Client

    def initialize(self) -> None:
        objects = self._get_objects(OBJECTS_TEST_FILE)
        self._create_templates_bucket(objects)

    def _get_objects(self, file: str) -> dict:
        return json.load(open(file))

    def _create_templates_bucket(self, objects: dict) -> None:
        self.s3.create_bucket(Bucket=TEMPLATES_BUCKET_NAME)
        for object in objects:
            if object["bucket"] == TEMPLATES_BUCKET_NAME:
                templates = object["objects"]
                for template in templates:
                    self.s3.put_object(
                        Bucket=TEMPLATES_BUCKET_NAME,
                        Key=template["key"],
                        Body=open(template["file"], "rb").read(),
                    )


@dataclass
class MockSQS:
    """
    MockSQS
    """

    sqs: SQSClient

    def initialize(self) -> None:
        self._create_newsletters_queue()
        self._create_news_summaries_queue()

    def _create_newsletters_queue(self) -> None:
        self.sqs.create_queue(QueueName=NEWSLETTERS_QUEUE_NAME)

    def _create_news_summaries_queue(self) -> None:
        self.sqs.create_queue(QueueName=NEWS_SUMMARIES_QUEUE_NAME)
