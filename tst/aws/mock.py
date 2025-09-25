import json
from dataclasses import dataclass

from mypy_boto3_s3.client import S3Client
from mypy_boto3_secretsmanager.client import SecretsManagerClient
from mypy_boto3_sqs import SQSClient

from src.environment import Domain
from src.media.bucket import MediaBucket
from tst.constants import (
    SECRETS_TEST_FILE,
    SYNC_TRANSACTIONS_TASK_QUEUE_NAME,
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
        self._create_bucket(MediaBucket._get_bucket_name(Domain.TESTING))

    def _create_bucket(self, bucket_name: str) -> None:
        self.s3.create_bucket(Bucket=bucket_name)


@dataclass
class MockSQS:
    """
    MockSQS
    """

    sqs: SQSClient

    def initialize(self) -> None:
        self.sqs.create_queue(QueueName=SYNC_TRANSACTIONS_TASK_QUEUE_NAME)
