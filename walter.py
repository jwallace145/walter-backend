from src.api.routing.router import APIRouter
from src.canaries.auth_user import AuthUserCanary
from src.canaries.get_news_summary import GetNewsSummaryCanary
from src.canaries.get_newsletters import GetNewslettersCanary
from src.canaries.get_portfolio import GetPortfolioCanary
from src.canaries.get_prices import GetPricesCanary
from src.canaries.get_stock import GetStockCanary
from src.canaries.get_transactions import GetTransactionsCanary
from src.canaries.get_user import GetUserCanary
from src.canaries.search_stocks import SearchStocksCanary
from src.clients import (
    walter_cw,
    walter_authenticator,
)


##############
# WALTER API #
##############


def walter_api_entrypoint(event, context) -> dict:
    return APIRouter.get_method(event).invoke(event).to_json()


###################
# WALTER CANARIES #
###################

# TODO: Create a canary router for each entrypoint


def auth_user_canary_entrypoint(event, context) -> dict:
    return AuthUserCanary(walter_cw).invoke()


def get_transactions_canary_entrypoint(event, context) -> dict:
    return GetTransactionsCanary(walter_authenticator, walter_cw).invoke()


def get_user_canary_entrypoint(event, context) -> dict:
    return GetUserCanary(walter_authenticator, walter_cw).invoke()


def get_stock_canary_entrypoint(event, context) -> dict:
    return GetStockCanary(walter_cw).invoke()


def get_portfolio_canary_entrypoint(event, context) -> dict:
    return GetPortfolioCanary(walter_authenticator, walter_cw).invoke()


def get_prices_canary_entrypoint(event, context) -> dict:
    return GetPricesCanary(walter_cw).invoke()


def get_news_summary_canary_entrypoint(event, context) -> dict:
    return GetNewsSummaryCanary(walter_cw).invoke()


def get_newsletters_canary_entrypoint(event, context) -> dict:
    return GetNewslettersCanary(walter_authenticator, walter_cw).invoke()


def search_stocks_canary_entrypoint(event, context) -> dict:
    return SearchStocksCanary(walter_cw).invoke()
