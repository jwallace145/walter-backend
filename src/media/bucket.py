from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from src.aws.s3.client import WalterS3Client
from src.environment import Domain
from src.utils.log import Logger

LOG = Logger(__name__).get_logger()


class MediaPrivacyType(Enum):

    PUBLIC = "public"
    PRIVATE = "private"

    def get_folder_name(self) -> str:
        return self.value


@dataclass
class MediaBucket:
    """
    Media Bucket
    """

    NAME_FORMAT = "walter-backend-media-{domain}"

    client: WalterS3Client
    domain: Domain

    def __post_init__(self) -> None:
        self.bucket = MediaBucket._get_bucket_name(self.domain)
        LOG.debug(
            f"Initializing MediaBucket client ({self.domain.value}) with bucket name: {self.bucket}"
        )

    def does_public_file_exist(self, key: str) -> Tuple[bool, Optional[str]]:
        file_exists: bool = self._check_if_file_exists(key, MediaPrivacyType.PUBLIC)
        s3_uri: Optional[str] = None
        if file_exists:
            s3_uri = self.get_public_s3_uri(key)
        return file_exists, s3_uri

    def does_private_file_exist(self, key: str) -> bool:
        return self._check_if_file_exists(key, MediaPrivacyType.PRIVATE)

    def upload_public_contents(self, name: str, contents: str) -> str:
        return self._stream_contents(name, contents, MediaPrivacyType.PUBLIC)

    def upload_private_contents(self, name: str, contents: str) -> None:
        return self._stream_contents(name, contents, MediaPrivacyType.PRIVATE)

    def _stream_contents(
        self, key: str, contents: str, privacy_type: MediaPrivacyType
    ) -> str:
        full_key: str = MediaBucket._get_key_name(key, privacy_type)
        LOG.debug(
            f"Uploading '{privacy_type.value}' file '{key}' to bucket '{self.bucket}'"
        )
        s3_uri: str = self.client.put_object(self.bucket, full_key, contents)
        LOG.debug(
            f"Uploaded '{privacy_type.value}' file '{key}' to bucket '{self.bucket}'"
        )
        return s3_uri

    def _check_if_file_exists(self, key: str, privacy_type: MediaPrivacyType) -> bool:
        full_key: str = MediaBucket._get_key_name(key, privacy_type)
        LOG.debug(
            f"Checking if '{privacy_type.value}' file with key '{full_key}' exists in bucket '{self.bucket}'"
        )
        if self.client.does_object_exist(self.bucket, key):
            LOG.debug(
                f"'{privacy_type.value}' file with key '{full_key}' exists in bucket '{self.bucket}'"
            )
            return True
        else:
            LOG.debug(
                f"'{privacy_type.value}' file with key '{full_key}' does not exist in bucket '{self.bucket}'"
            )
            return False

    def get_public_s3_uri(self, key: str) -> str:
        return self._get_s3_uri(MediaPrivacyType.PUBLIC, key)

    def get_private_s3_uri(self, key: str) -> str:
        return self._get_s3_uri(MediaPrivacyType.PRIVATE, key)

    def _get_s3_uri(self, privacy_type: MediaPrivacyType, key: str) -> str:
        return WalterS3Client.get_uri(
            bucket=self.bucket, key=MediaBucket._get_key_name(key, privacy_type)
        )

    @staticmethod
    def _get_key_name(name: str, privacy_type: MediaPrivacyType) -> str:
        return f"{privacy_type.get_folder_name()}/{name}"

    @staticmethod
    def _get_bucket_name(domain: Domain) -> str:
        return MediaBucket.NAME_FORMAT.format(domain=domain.value)
