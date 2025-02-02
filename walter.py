from src.api.add_stock import AddStock
from src.api.auth_user import AuthUser
from src.api.change_password import ChangePassword
from src.api.create_user import CreateUser
from src.api.delete_stock import DeleteStock
from src.api.get_news_summary import GetNewsSummary
from src.api.get_portfolio import GetPortfolio
from src.api.get_prices import GetPrices
from src.api.get_stock import GetStock
from src.api.get_user import GetUser
from src.api.search_stocks import SearchStocks
from src.api.send_change_password_email import SendChangePasswordEmail
from src.api.send_newsletter import SendNewsletter
from src.api.send_verify_email import SendVerifyEmail
from src.api.subscribe import Subscribe
from src.api.unsubscribe import Unsubscribe
from src.api.verify_email import VerifyEmail
from src.backend.backend import create_newsletter_and_send
from src.clients import (
    walter_cw,
    walter_db,
    walter_sm,
    walter_stocks_api,
    newsletters_queue,
    walter_authenticator,
    template_engine,
    templates_bucket,
    walter_ses,
    news_summaries_bucket,
    walter_ai,
)
from src.newsletters.publish import add_newsletter_to_queue


##############
# WALTER API #
##############


def create_user_entrypoint(event, context) -> dict:
    return CreateUser(
        walter_authenticator,
        walter_cw,
        walter_db,
        walter_ses,
        template_engine,
        templates_bucket,
    ).invoke(event)


def auth_user_entrypoint(event, context) -> dict:
    return AuthUser(walter_authenticator, walter_cw, walter_db, walter_sm).invoke(event)


def get_user_entrypoint(event, context) -> dict:
    return GetUser(walter_authenticator, walter_cw, walter_db, walter_sm).invoke(event)


def get_stock_entrypoint(event, context) -> dict:
    return GetStock(
        walter_authenticator, walter_cw, walter_db, walter_stocks_api
    ).invoke(event)


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


def get_news_summary_entrypoint(event, context) -> dict:
    return GetNewsSummary(
        walter_authenticator,
        walter_cw,
        walter_db,
        walter_stocks_api,
        walter_ai,
        news_summaries_bucket,
    ).invoke(event)


def send_newsletter_entrypoint(event, context) -> dict:
    return SendNewsletter(
        walter_authenticator, walter_cw, walter_db, newsletters_queue, walter_sm
    ).invoke(event)


def get_prices_entrypoint(event, context) -> dict:
    return GetPrices(
        walter_authenticator, walter_cw, walter_db, walter_stocks_api
    ).invoke(event)


def verify_email_entrypoint(event, context) -> dict:
    return VerifyEmail(walter_authenticator, walter_cw, walter_db).invoke(event)


def send_verify_email_entrypoint(event, context) -> dict:
    return SendVerifyEmail(
        walter_authenticator,
        walter_cw,
        walter_db,
        walter_ses,
        template_engine,
        templates_bucket,
    ).invoke(event)


def change_password_entrypoint(event, context) -> dict:
    return ChangePassword(walter_authenticator, walter_cw, walter_db).invoke(event)


def send_change_password_email_entrypoint(event, context) -> dict:
    return SendChangePasswordEmail(
        walter_authenticator,
        walter_cw,
        walter_db,
        walter_ses,
        template_engine,
        templates_bucket,
    ).invoke(event)


def subscribe_entrypoint(event, context) -> dict:
    return Subscribe(walter_authenticator, walter_cw, walter_db).invoke(event)


def unsubscribe_entrypoint(event, context) -> dict:
    return Unsubscribe(walter_authenticator, walter_cw, walter_db).invoke(event)


def search_stocks_entrypoint(event, context) -> dict:
    return SearchStocks(walter_authenticator, walter_cw, walter_stocks_api).invoke(event)


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
