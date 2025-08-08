from dataclasses import dataclass

from enum import Enum
from src.canaries.common.canary import BaseCanary
from src.canaries.get_portfolio import GetPortfolioCanary
from src.canaries.get_prices import GetPricesCanary
from src.canaries.get_stock import GetStockCanary
from src.canaries.get_transactions import GetTransactionsCanary
from src.canaries.get_user import GetUserCanary
from src.clients import walter_cw, walter_authenticator
from src.utils.log import Logger
from src.canaries.auth_user import AuthUserCanary

log = Logger(__name__).get_logger()


class CanaryType(Enum):
    AUTH_USER = "auth_user"
    GET_PORTFOLIO = "get_portfolio"
    GET_PRICES = "get_prices"
    GET_STOCK = "get_stock"
    GET_USER = "get_user"
    GET_TRANSACTIONS = "get_transactions"


@dataclass
class CanaryRouter:

    @staticmethod
    def get_canary(event: dict) -> BaseCanary:
        log.info(f"Received event: {event}")
        canary = event["canary"]
        log.info(f"Canary: {canary}")

        match canary:
            case CanaryType.AUTH_USER.value:
                return AuthUserCanary(walter_cw)
            case CanaryType.GET_PORTFOLIO.value:
                return GetPortfolioCanary(walter_authenticator, walter_cw)
            case CanaryType.GET_PRICES.value:
                return GetPricesCanary(walter_cw)
            case CanaryType.GET_STOCK.value:
                return GetStockCanary(walter_cw)
            case CanaryType.GET_USER.value:
                return GetUserCanary(walter_authenticator, walter_cw)
            case CanaryType.GET_TRANSACTIONS.value:
                return GetTransactionsCanary(walter_authenticator, walter_cw)
            case _:
                raise Exception(f"Canary {canary} not found.")
