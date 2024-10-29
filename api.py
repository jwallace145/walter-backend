from src.api.add_stock import AddStock
from src.api.auth_user import AuthUser
from src.api.create_user import CreateUser
from src.api.get_portfolio import GetPortfolio
from src.api.get_prices import GetPrices
from src.api.get_user import GetUser
from src.api.send_newsletter import SendNewsletter
from src.clients import walter_db, newsletters_queue, sm, walter_stocks_api, walter_cw
from src.utils.log import Logger

log = Logger(__name__).get_logger()

############
# HANDLERS #
############


def auth_user(event, context) -> dict:
    return AuthUser(walter_cw, walter_db, sm).invoke(event)


def create_user(event, context) -> dict:
    return CreateUser(walter_cw, walter_db).invoke(event)


def get_user(event, context) -> dict:
    return GetUser(walter_cw, walter_db, sm).invoke(event)


def add_stock(event, context) -> dict:
    return AddStock(walter_cw, walter_db, walter_stocks_api, sm).invoke(event)


def get_portfolio(event, context) -> dict:
    return GetPortfolio(walter_cw, walter_db, sm, walter_stocks_api).invoke(event)


def send_newsletter(event, context) -> dict:
    return SendNewsletter(walter_cw, walter_db, newsletters_queue, sm).invoke(event)


def get_prices(event, context) -> dict:
    return GetPrices(walter_cw, walter_db, walter_stocks_api).invoke(event)
