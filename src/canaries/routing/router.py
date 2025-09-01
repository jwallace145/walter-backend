from dataclasses import dataclass
from enum import Enum

from src.canaries.accounts.get_accounts import GetAccounts
from src.canaries.auth.login import Login
from src.canaries.auth.logout import Logout
from src.canaries.auth.refresh import Refresh
from src.canaries.common.canary import BaseCanary
from src.canaries.transactions.get_transactions import GetTransactions
from src.canaries.users.get_user import GetUser
from src.clients import AUTHENTICATOR, DATABASE, DATADOG
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

    @staticmethod
    def get_canary(canary_type: CanaryType) -> BaseCanary:
        log.info(f"Getting '{canary_type.value}' canary'")

        match canary_type:
            case CanaryType.LOGIN:
                return Login(AUTHENTICATOR, DATABASE, DATADOG)
            case CanaryType.REFRESH:
                return Refresh(AUTHENTICATOR, DATABASE, DATADOG)
            case CanaryType.LOGOUT:
                return Logout(AUTHENTICATOR, DATABASE, DATADOG)
            case CanaryType.GET_USER:
                return GetUser(AUTHENTICATOR, DATABASE, DATADOG)
            case CanaryType.GET_ACCOUNTS:
                return GetAccounts(AUTHENTICATOR, DATABASE, DATADOG)
            case CanaryType.GET_TRANSACTIONS:
                return GetTransactions(AUTHENTICATOR, DATABASE, DATADOG)
            case _:
                raise Exception(f"Canary type {canary_type} not found.")
