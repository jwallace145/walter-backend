from src.api.add_stock import AddStock
from src.api.auth_user import AuthUser
from src.api.create_user import CreateUser
from src.api.delete_stock import DeleteStock
from src.api.get_news import GetNews
from src.api.get_portfolio import GetPortfolio
from src.api.get_prices import GetPrices
from src.api.get_user import GetUser
from src.api.send_newsletter import SendNewsletter
from src.backend.backend import create_newsletter_and_send
from src.clients import (
    walter_cw,
    walter_db,
    walter_sm,
    walter_stocks_api,
    newsletters_queue,
    walter_authenticator,
)
from src.newsletters.publish import add_newsletter_to_queue


##############
# WALTER API #
##############


def create_user_entrypoint(event, context) -> dict:
    return CreateUser(walter_authenticator, walter_cw, walter_db).invoke(event)


def auth_user_entrypoint(event, context) -> dict:
    return AuthUser(walter_authenticator, walter_cw, walter_db, walter_sm).invoke(event)


def get_user_entrypoint(event, context) -> dict:
    return GetUser(walter_authenticator, walter_cw, walter_db, walter_sm).invoke(event)


def add_stock_entrypoint(event, context) -> dict:
    return AddStock(
        walter_authenticator, walter_cw, walter_db, walter_stocks_api, walter_sm
    ).invoke(event)


def delete_stock_entrypoint(event, context) -> dict:
    return DeleteStock(
        walter_authenticator, walter_cw, walter_db, walter_stocks_api, walter_sm
    ).invoke(event)


def get_portfolio_entrypoint(event, context) -> dict:
    return GetPortfolio(
        walter_authenticator, walter_cw, walter_db, walter_sm, walter_stocks_api
    ).invoke(event)


def get_news_entrypoint(event, context) -> dict:
    return GetNews(
        walter_authenticator, walter_cw, walter_db, walter_stocks_api
    ).invoke(event)


def send_newsletter_entrypoint(event, context) -> dict:
    return SendNewsletter(
        walter_authenticator, walter_cw, walter_db, newsletters_queue, walter_sm
    ).invoke(event)


def get_prices_entrypoint(event, context) -> dict:
    return GetPrices(
        walter_authenticator, walter_cw, walter_db, walter_stocks_api
    ).invoke(event)


######################
# WALTER NEWSLETTERS #
######################


def add_newsletter_to_queue_entrypoint(event, context) -> dict:
    return add_newsletter_to_queue(event, context)


##################
# WALTER BACKEND #
##################


def create_newsletter_and_send_entrypoint(event, context) -> dict:
    return create_newsletter_and_send(event, context)
