from dataclasses import dataclass
from enum import Enum

from src.canaries.accounts.get_accounts import GetAccounts
from src.canaries.auth.login import Login
from src.canaries.auth.logout import Logout
from src.canaries.auth.refresh import Refresh
from src.canaries.common.canary import BaseCanary
from src.canaries.transactions.get_transactions import GetTransactions
from src.canaries.users.create_user import CreateUser
from src.canaries.users.get_user import GetUser
from src.environment import AWS_REGION, DOMAIN
from src.factory import ClientFactory
from src.utils.log import Logger

log = Logger(__name__).get_logger()


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

    @classmethod
    def from_string(cls, canary_type_str: str):
        for canary_type in CanaryType:
            if canary_type.value.lower() == canary_type_str.lower():
                return canary_type
        raise ValueError(f"Invalid canary type '{canary_type_str}'!")


@dataclass
class CanaryRouter:
    """Router for Canaries"""

    # set during post-init
    client_factory: ClientFactory = None

    def __post_init__(self) -> None:
        log.debug("Initializing CanaryRouter")
        self.client_factory = ClientFactory(region=AWS_REGION, domain=DOMAIN)

    def get_canary(self, canary_type: CanaryType) -> BaseCanary:
        log.info(f"Getting '{canary_type.value}' canary'")

        match canary_type:
            case CanaryType.LOGIN:
                return Login(
                    authenticator=self.client_factory.get_authenticator(),
                    db=self.client_factory.get_db_client(),
                    metrics=self.client_factory.get_metrics_client(),
                )
            case CanaryType.REFRESH:
                return Refresh(
                    authenticator=self.client_factory.get_authenticator(),
                    db=self.client_factory.get_db_client(),
                    metrics=self.client_factory.get_metrics_client(),
                )
            case CanaryType.LOGOUT:
                return Logout(
                    authenticator=self.client_factory.get_authenticator(),
                    db=self.client_factory.get_db_client(),
                    metrics=self.client_factory.get_metrics_client(),
                )
            case CanaryType.GET_USER:
                return GetUser(
                    authenticator=self.client_factory.get_authenticator(),
                    db=self.client_factory.get_db_client(),
                    metrics=self.client_factory.get_metrics_client(),
                )
            case CanaryType.CREATE_USER:
                return CreateUser(
                    authenticator=self.client_factory.get_authenticator(),
                    db=self.client_factory.get_db_client(),
                    metrics=self.client_factory.get_metrics_client(),
                )
            case CanaryType.GET_ACCOUNTS:
                return GetAccounts(
                    authenticator=self.client_factory.get_authenticator(),
                    db=self.client_factory.get_db_client(),
                    metrics=self.client_factory.get_metrics_client(),
                )
            case CanaryType.GET_TRANSACTIONS:
                return GetTransactions(
                    authenticator=self.client_factory.get_authenticator(),
                    db=self.client_factory.get_db_client(),
                    metrics=self.client_factory.get_metrics_client(),
                )
            case _:
                raise Exception(f"Canary type {canary_type} not found.")
