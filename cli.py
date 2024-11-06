import json

import typer

from api import (
    auth_user as AUTH_USER_API,
    add_stock as ADD_STOCK_API,
    create_user as CREATE_USER_API,
    get_portfolio as GET_PORTFOLIO_API,
    get_user as GET_USER_API,
    send_newsletter as SEND_NEWSLETTER_API,
)
from newsletters import send_messages
from src.utils.log import Logger
from tst.api.utils import (
    get_auth_user_event,
    get_create_user_event,
    get_get_user_event,
    get_add_stock_event,
    get_portfolio_event,
    get_send_newsletter_event,
)
from tst.utils.utils import get_walter_backend_event
from walter import lambda_handler

log = Logger(__name__).get_logger()

CONTEXT = {}


def parse_response(response: dict) -> str:
    response["body"] = json.loads(response["body"])
    return json.dumps(response, indent=4)


##############
# WALTER CLI #
##############

app = typer.Typer()

##############
# WALTER API #
##############


@app.command()
def auth_user(email: str = None, password: str = None) -> None:
    log.info("Walter CLI: Authenticating user...")
    event = get_auth_user_event(email, password)
    response = AUTH_USER_API(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def create_user(email: str = None, username: str = None, password: str = None) -> None:
    log.info("Walter CLI: Creating user...")
    event = get_create_user_event(email, username, password)
    response = CREATE_USER_API(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def get_user(token: str = None) -> None:
    log.info("Walter CLI: Getting user...")
    event = get_get_user_event(token)
    response = GET_USER_API(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def add_stock(token: str = None, stock: str = None, quantity: float = None) -> None:
    log.info("Walter CLI: Adding stock...")
    event = get_add_stock_event(stock, quantity, token)
    response = ADD_STOCK_API(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def get_portfolio(token: str = None) -> None:
    log.info("Walter CLI: Getting portfolio...")
    event = get_portfolio_event(token)
    response = GET_PORTFOLIO_API(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def send_newsletter(token: str = None) -> None:
    log.info("Walter CLI: Sending newsletter...")
    event = get_send_newsletter_event(token)
    response = SEND_NEWSLETTER_API(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


###########################
# WALTER SEND NEWSLETTERS #
###########################


@app.command()
def send_newsletters():
    log.info("Walter CLI: Sending newsletters to all users...")
    send_messages({}, CONTEXT)


##################
# WALTER BACKEND #
##################


@app.command()
def walter_backend(email: str = None) -> None:
    log.info("Walter CLI: Invoking WalterBackend...")
    event = get_walter_backend_event(email)
    response = lambda_handler(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


if __name__ == "__main__":
    app()
