import json
from dataclasses import dataclass
from io import BytesIO
from typing import List, Tuple

from botocore.exceptions import ClientError
from mypy_boto3_s3 import S3Client

from src.environment import Domain
from src.utils.log import Logger
import datetime as dt

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
                f"Objects from S3 with prefix '{WalterS3Client.get_uri(bucket, prefix)}':\n{json.dumps(objects, indent=4)}"
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
            log.warning(
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

    def put_object(
        self, bucket: str, key: str, contents: str, content_type: str = None
    ) -> str:
        s3_uri = WalterS3Client.get_uri(bucket, key)
        log.debug(f"Putting object to S3 with URI '{s3_uri}'")

        try:
            kwargs = {"Bucket": bucket, "Key": key, "Body": contents}

            # add content type to keyword args if given
            if content_type:
                kwargs["ContentType"] = "image/jpeg"

            self.client.put_object(**kwargs)
            log.debug(f"Put object to S3 with URI '{s3_uri}' successfully!")
            return s3_uri
        except ClientError as error:
            log.error(
                f"Unexpected error occurred putting object to S3 with URI '{s3_uri}'!",
                error,
            )
            raise error

    def create_presigned_get_object_url(
        self, bucket: str, key: str, expiration_in_seconds: int = 3600
    ) -> Tuple[str, dt.datetime]:
        """
        Create a presigned URL to get an object from S3.

        Walter S3 buckets are private to ensure controlled access. However, Walter
        needs to access certain media assets from S3 to render the frontend (e.g.
        profile pictures). So, this method creates a presigned URL to allow for
        limited access to the object. This ensures that the required media stored
        by Walter can be accessed by the frontend but not by anyone else.

        Args:
            bucket: The name of the S3 bucket.
            key: The key of the object stored in the bucket.
            expiration_in_seconds: The length of time in seconds that the presigned URL is valid for.

        Returns:
            presigned_url: A presigned URL to get the object from S3.
        """
        s3_uri = WalterS3Client.get_uri(bucket, key)
        log.debug(f"Creating presigned GetObject URL for object '{s3_uri}'")
        try:
            now = dt.datetime.now(dt.UTC)
            presigned_url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expiration_in_seconds,
            )
            # TODO: you can get expiration time from presigned URL query string param epoch value
            expiration = now + dt.timedelta(seconds=expiration_in_seconds)
            log.debug(
                f"Created presigned GetObject URL for object '{s3_uri}' successfully!"
            )
            return presigned_url, expiration
        except ClientError as error:
            log.error(
                f"Unexpected error occurred creating presigned GetObject URL for object '{s3_uri}'!",
                error,
            )
            raise error

    def upload_file(self, file_path: str, bucket: str, key: str) -> str:
        """
        Upload a file to an S3 bucket.

        Args:
            file_path: Path to file to upload
            bucket: Bucket to upload to
            key: S3 object name

        Returns:
            s3_uri: URI of uploaded file in S3
        """
        s3_uri = WalterS3Client.get_uri(bucket, key)
        log.debug(f"Uploading file '{file_path}' to S3 with URI '{s3_uri}'")
        try:
            self.client.upload_file(Filename=file_path, Bucket=bucket, Key=key)
            log.debug(f"Uploaded file to S3 with URI '{s3_uri}' successfully!")
            return s3_uri
        except ClientError as error:
            log.error(
                f"Unexpected error occurred uploading file to S3 with URI '{s3_uri}'!",
                error,
            )
            raise error

    def get_public_url(self, bucket: str, key: str) -> str:
        return f"https://{bucket}.s3.{self.client.meta.region_name}.amazonaws.com/{key}"

    @staticmethod
    def get_uri(bucket: str, key: str) -> str:
        return f"s3://{bucket}/{key}"

    @staticmethod
    def get_bucket_and_key(uri: str) -> Tuple[str, str]:
        bucket = uri.split("s3://")[1].split("/")[0]
        key = "/".join(uri.split("s3://")[1].split("/")[1:])
        return bucket, key
