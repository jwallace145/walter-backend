from dataclasses import dataclass
from enum import Enum
from typing import Tuple

from src.aws.sts.client import WalterSTSClient
from src.canaries.accounts.get_accounts import GetAccounts
from src.canaries.auth.login import Login
from src.canaries.auth.logout import Logout
from src.canaries.auth.refresh import Refresh
from src.canaries.common.canary import BaseCanary
from src.canaries.transactions.get_transactions import GetTransactions
from src.canaries.transactions.update_transaction import UpdateTransaction
from src.canaries.users.create_user import CreateUser
from src.canaries.users.get_user import GetUser
from src.factory import ClientFactory
from src.utils.log import Logger

LOG = Logger(__name__).get_logger()


class CanaryType(Enum):
    """Supported Canary Types"""

    ##################
    # AUTHENTICATION #
    ##################

    LOGIN = "Login"
    REFRESH = "Refresh"
    LOGOUT = "Logout"

    #########
    # USERS #
    #########

    GET_USER = "GetUser"
    CREATE_USER = "CreateUser"

    ############
    # ACCOUNTS #
    ############

    GET_ACCOUNTS = "GetAccounts"

    ################
    # TRANSACTIONS #
    ################

    GET_TRANSACTIONS = "GetTransactions"
    UPDATE_TRANSACTION = "UpdateTransaction"

    def get_canary_name(self) -> str:
        return self.value

    @classmethod
    def from_string(cls, canary_type_str: str):
        for canary_type in CanaryType:
            if canary_type.value.lower() == canary_type_str.lower():
                return canary_type
        raise ValueError(f"Invalid canary type '{canary_type_str}'!")


@dataclass(kw_only=True)
class CanaryFactory:

    # Canary IAM role name format must stay in sync with Terraform name format for all canaries
    CANARY_ROLE_NAME_FORMAT = "WalterBackend-Canary-{method}-Role-{domain}"

    client_factory: ClientFactory
    api_key: str

    def __post_init__(self) -> None:
        LOG.debug("Creating CanaryFactory")

    def get_canary(self, canary_type: CanaryType) -> BaseCanary:
        LOG.info(f"Getting canary of type: '{canary_type.value}'")

        credentials: Tuple[str, str, str] = self.get_canary_credentials(canary_type)
        aws_access_key_id, aws_secret_access_key, aws_session_token = credentials

        self.client_factory.set_aws_credentials(
            aws_access_key_id, aws_secret_access_key, aws_session_token
        )

        match canary_type:
            case CanaryType.LOGIN:
                return Login(
                    api_key=self.api_key,
                    authenticator=self.client_factory.get_authenticator(),
                    db=self.client_factory.get_db_client(),
                    metrics=self.client_factory.get_metrics_client(),
                )
            case CanaryType.REFRESH:
                return Refresh(
                    api_key=self.api_key,
                    authenticator=self.client_factory.get_authenticator(),
                    db=self.client_factory.get_db_client(),
                    metrics=self.client_factory.get_metrics_client(),
                )
            case CanaryType.LOGOUT:
                return Logout(
                    api_key=self.api_key,
                    authenticator=self.client_factory.get_authenticator(),
                    db=self.client_factory.get_db_client(),
                    metrics=self.client_factory.get_metrics_client(),
                )
            case CanaryType.GET_USER:
                return GetUser(
                    api_key=self.api_key,
                    authenticator=self.client_factory.get_authenticator(),
                    db=self.client_factory.get_db_client(),
                    metrics=self.client_factory.get_metrics_client(),
                )
            case CanaryType.CREATE_USER:
                return CreateUser(
                    api_key=self.api_key,
                    authenticator=self.client_factory.get_authenticator(),
                    db=self.client_factory.get_db_client(),
                    metrics=self.client_factory.get_metrics_client(),
                )
            case CanaryType.GET_ACCOUNTS:
                return GetAccounts(
                    api_key=self.api_key,
                    authenticator=self.client_factory.get_authenticator(),
                    db=self.client_factory.get_db_client(),
                    metrics=self.client_factory.get_metrics_client(),
                )
            case CanaryType.GET_TRANSACTIONS:
                return GetTransactions(
                    api_key=self.api_key,
                    authenticator=self.client_factory.get_authenticator(),
                    db=self.client_factory.get_db_client(),
                    metrics=self.client_factory.get_metrics_client(),
                )
            case CanaryType.UPDATE_TRANSACTION:
                return UpdateTransaction(
                    api_key=self.api_key,
                    authenticator=self.client_factory.get_authenticator(),
                    db=self.client_factory.get_db_client(),
                    metrics=self.client_factory.get_metrics_client(),
                )
            case _:
                raise Exception(f"Canary type {canary_type} not found.")

    def get_canary_credentials(self, canary_type: CanaryType) -> Tuple[str, str, str]:
        LOG.info(f"Getting credentials for '{canary_type.value}' canary")
        domain: str = self.client_factory.get_domain().value

        role_name = self.CANARY_ROLE_NAME_FORMAT.format(
            method=canary_type.get_canary_name(), domain=domain
        )

        LOG.info(f"Assuming role '{role_name}'")
        sts: WalterSTSClient = self.client_factory.get_sts_client()
        credentials = sts.assume_role(
            role_name,
            f"{canary_type.get_canary_name()}-Canary-Session-{domain}",
        )
        LOG.info(f"Assumed role '{role_name}' successfully!'")

        # get credentials from assume role response api call
        aws_access_key_id = credentials["AccessKeyId"]
        aws_secret_access_key = credentials["SecretAccessKey"]
        aws_session_token = credentials["SessionToken"]

        return aws_access_key_id, aws_secret_access_key, aws_session_token
