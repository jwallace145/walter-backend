from dataclasses import dataclass

from src.aws.s3.client import WalterS3Client
from src.environment import Domain
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class PublicMediaBucket:
    """
    Public Media Bucket
    """

    NAME_FORMAT = "walterai-public-media-{domain}"

    STOCKS_DIR = "stocks"
    STOCK_LOGO_KEY_FORMAT = "{stocks_dir}/{symbol}/logo.svg"
    STOCK_ICON_KEY_FORMAT = "{stocks_dir}/{symbol}/icon.png"

    client: WalterS3Client
    domain: Domain

    def __post_init__(self) -> None:
        self.bucket = PublicMediaBucket._get_bucket_name(self.domain)
        log.debug(f"Creating PublicMediaBucket with bucket name: {self.bucket}")

    def get_stock_logo_url(self, symbol: str) -> str:
        log.info(f"Getting stock '{symbol.upper()}' logo from bucket '{self.bucket}'")
        return self.client.get_public_url(
            bucket=self.bucket, key=PublicMediaBucket._get_logo_key(symbol)
        )

    def get_stock_icon_url(self, symbol: str) -> str:
        log.info(f"Getting stock '{symbol.upper()}' icon from bucket '{self.bucket}'")
        return self.client.get_public_url(
            bucket=self.bucket, key=PublicMediaBucket._get_icon_key(symbol)
        )

    @staticmethod
    def _get_bucket_name(domain: Domain) -> str:
        return PublicMediaBucket.NAME_FORMAT.format(domain=domain.value)

    @staticmethod
    def _get_logo_key(symbol: str) -> str:
        return PublicMediaBucket.STOCK_LOGO_KEY_FORMAT.format(
            stocks_dir=PublicMediaBucket.STOCKS_DIR, symbol=symbol.lower()
        )

    @staticmethod
    def _get_icon_key(symbol: str) -> str:
        return PublicMediaBucket.STOCK_ICON_KEY_FORMAT.format(
            stocks_dir=PublicMediaBucket.STOCKS_DIR, symbol=symbol.lower()
        )
