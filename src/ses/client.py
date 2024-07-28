from dataclasses import dataclass
from src.utils.log import Logger
from src.environment import Domain
from mypy_boto3_ses import SESClient

log = Logger(__name__).get_logger()


@dataclass
class SESClient:
    """
    WalterAI Simple Email Service (SES) Client
    """

    client: SESClient
    domain: Domain

    def __post_init__(self) -> None:
        log.debug(
            f"Creating {self.domain.value} SES Client in region '{self.client.meta.region_name}'"
        )
