from dataclasses import dataclass

from botocore.exceptions import ClientError
from mypy_boto3_sts import STSClient
from mypy_boto3_sts.type_defs import CredentialsTypeDef

from src.environment import Domain
from src.utils.log import Logger

LOG = Logger(__name__).get_logger()


@dataclass(kw_only=True)
class WalterSTSClient:

    region: str
    domain: Domain
    client: STSClient

    def __post_init__(self) -> None:
        LOG.debug(
            f"WalterSTSClient initialized in region '{self.region}' with domain: {self.domain.value}"
        )

    def assume_role(self, role_name: str, role_session_name: str) -> CredentialsTypeDef:
        LOG.debug(
            f"Assuming role with name '{role_name}' with session name '{role_session_name}'"
        )
        role_arn: str = self._get_role_arn(role_name)
        LOG.debug(f"Constructed role ARN to assume: '{role_arn}'")
        try:
            credentials = self.client.assume_role(
                RoleArn=role_arn, RoleSessionName=role_session_name
            )["Credentials"]
            LOG.debug(f"Assumed role with credentials: {credentials}")
            return credentials
        except ClientError as error:
            LOG.error(
                f"Unexpected error occurred assuming role ARN '{role_arn}'\n"
                f"Error: {error.response['Error']['Message']}"
            )
            raise error

    def get_caller_identity(self) -> str:
        LOG.debug("Getting caller identity")
        try:
            return self.client.get_caller_identity()["Arn"]
        except ClientError as error:
            LOG.error(
                f"Unexpected error occurred getting caller identity!\n"
                f"Error: {error.response['Error']['Message']}"
            )
            raise error

    def _get_role_arn(self, role_name: str) -> str:
        return f"arn:aws:iam::010526272437:role/{role_name}"
