from dataclasses import dataclass
from io import BytesIO
from typing import List

from botocore.exceptions import ClientError
from mypy_boto3_s3 import S3Client
from src.environment import Domain
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class WalterS3Client:
    """
    WalterAIBackend S3 Client

    Boto3 S3 client wrapper class.
    """

    client: S3Client
    domain: Domain

    def __post_init__(self) -> None:
        log.debug(
            f"Creating '{self.domain.value}' WalterAIBackend S3 client in region '{self.client.meta.region_name}'"
        )

    def list_objects(self, bucket: str, prefix: str) -> List[str]:
        log.debug(
            f"Listing objects from S3 with prefix '{WalterS3Client.get_uri(bucket, prefix)}'"
        )
        try:
            objects = [
                content["Key"]
                for content in self.client.list_objects_v2(
                    Bucket=bucket, Prefix=prefix
                )["Contents"]
            ]
            log.debug(
                f"Objects from S3 with prefix '{WalterS3Client.get_uri(bucket, prefix)}':\n{objects}"
            )
            return objects
        except ClientError as error:
            log.error(
                f"Unexpected error occurred listing objects with prefix '{WalterS3Client.get_uri(bucket, prefix)}'!",
                error,
            )
            raise error
        except KeyError:
            # TODO: Is there a better way to handle this?
            log.error(
                f"No contents returned with prefix '{WalterS3Client.get_uri(bucket, prefix)}'!"
            )
            return []

    def get_object(self, bucket: str, key: str) -> str | None:
        uri = WalterS3Client.get_uri(bucket, key)
        log.debug(f"Getting object from S3 with URI '{uri}'")
        try:
            object = (
                self.client.get_object(Bucket=bucket, Key=key)["Body"]
                .read()
                .decode("utf-8")
            )
            log.debug(f"Retrieved object from S3 with URI '{uri}'")
            return object
        except ClientError as error:
            # return none if key does not exist
            if error.response["Error"]["Code"] == "NoSuchKey":
                log.warning(f"Object with URI '{uri}' does not exist!")
                return None
            log.error(
                f"Unexpected error occurred getting object from S3 '{uri}'!",
                error,
            )
            raise error

    def download_object(self, bucket: str, key: str) -> BytesIO:
        log.debug(
            f"Downloading object from S3 with URI '{WalterS3Client.get_uri(bucket, key)}'"
        )
        try:
            stream = BytesIO()
            self.client.download_fileobj(Bucket=bucket, Key=key, Fileobj=stream)
            log.debug(
                f"Downloaded object from S3 with URI '{WalterS3Client.get_uri(bucket, key)}'"
            )
            return stream
        except ClientError as error:
            log.error(
                f"Unexpected error occurred downloading object from S3 with URI '{WalterS3Client.get_uri(bucket, key)}'!",
                error,
            )
            raise error

    def put_object(self, bucket: str, key: str, contents: str) -> str:
        log.debug(
            f"Putting object to S3 with URI '{WalterS3Client.get_uri(bucket, key)}'"
        )
        try:
            self.client.put_object(Bucket=bucket, Key=key, Body=contents)
            log.debug(
                f"Put object to S3 with URI '{WalterS3Client.get_uri(bucket, key)}' successfully!"
            )
            return WalterS3Client.get_uri(bucket, key)
        except ClientError as error:
            log.error(
                f"Unexpected error occurred putting object to S3 with URI '{WalterS3Client.get_uri(bucket, key)}'!",
                error,
            )
            raise error

    @staticmethod
    def get_uri(bucket: str, key: str) -> str:
        return f"s3://{bucket}/{key}"
