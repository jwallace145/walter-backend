import json

import typer

from src.newsletters.publish import add_newsletter_to_queue
from src.utils.log import Logger
from tst.api.utils import (
    get_auth_user_event,
    get_create_user_event,
    get_get_user_event,
    get_add_stock_event,
    get_portfolio_event,
    get_send_newsletter_event,
    get_news_event,
    get_send_verify_email_event,
    get_verify_email_event,
    get_change_password_event,
    get_send_change_password_email_event,
    get_get_stock_event,
    get_unsubscribe_event,
    get_subscribe_event,
)
from tst.events.utils import get_walter_backend_event
from walter import (
    auth_user_entrypoint,
    create_user_entrypoint,
    get_user_entrypoint,
    add_stock_entrypoint,
    get_portfolio_entrypoint,
    send_newsletter_entrypoint,
    create_newsletter_and_send_entrypoint,
    get_news_entrypoint,
    send_verify_email_entrypoint,
    verify_email_entrypoint,
    change_password_entrypoint,
    send_change_password_email_entrypoint,
    get_stock_entrypoint,
    unsubscribe_entrypoint,
    subscribe_entrypoint,
)

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
    response = auth_user_entrypoint(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def create_user(email: str = None, username: str = None, password: str = None) -> None:
    log.info("Walter CLI: Creating user...")
    event = get_create_user_event(email, username, password)
    response = create_user_entrypoint(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def get_user(token: str = None) -> None:
    log.info("Walter CLI: Getting user...")
    event = get_get_user_event(token)
    response = get_user_entrypoint(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def add_stock(token: str = None, stock: str = None, quantity: float = None) -> None:
    log.info("Walter CLI: Adding stock...")
    event = get_add_stock_event(stock, quantity, token)
    response = add_stock_entrypoint(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def get_portfolio(token: str = None) -> None:
    log.info("Walter CLI: Getting portfolio...")
    event = get_portfolio_event(token)
    response = get_portfolio_entrypoint(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def get_news(stock: str = None) -> None:
    log.info("Walter CLI: Getting news...")
    event = get_news_event(stock)
    response = get_news_entrypoint(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def send_newsletter(token: str = None) -> None:
    log.info("Walter CLI: Sending newsletter...")
    event = get_send_newsletter_event(token)
    response = send_newsletter_entrypoint(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def verify_email(token: str = None) -> None:
    log.info("Walter CLI: Verifying email...")
    event = get_verify_email_event(token)
    response = verify_email_entrypoint(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def send_verify_email(token: str = None) -> None:
    log.info("Walter CLI: Sending verify email...")
    event = get_send_verify_email_event(token)
    response = send_verify_email_entrypoint(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def change_password(token: str = None, new_password: str = None) -> None:
    log.info("Walter CLI: Changing password...")
    event = get_change_password_event(token, new_password)
    response = change_password_entrypoint(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def send_change_password_email(email: str = None) -> None:
    log.info("Walter CLI: Sending change password email...")
    event = get_send_change_password_email_event(email)
    response = send_change_password_email_entrypoint(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def get_stock(symbol: str = None) -> None:
    log.info("Walter CLI: Getting stock...")
    event = get_get_stock_event(symbol)
    response = get_stock_entrypoint(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def subscribe(token: str = None) -> None:
    log.info("Walter CLI: Subscribing user from newsletter...")
    event = get_subscribe_event(token)
    response = subscribe_entrypoint(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def unsubscribe(token: str = None) -> None:
    log.info("Walter CLI: Unsubscribing user from newsletter...")
    event = get_unsubscribe_event(token)
    response = unsubscribe_entrypoint(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


###########################
# WALTER SEND NEWSLETTERS #
###########################


@app.command()
def send_newsletters():
    log.info("Walter CLI: Sending newsletters to all users...")
    add_newsletter_to_queue({}, CONTEXT)


##################
# WALTER BACKEND #
##################


@app.command()
def walter_backend(email: str = None) -> None:
    log.info("Walter CLI: Invoking WalterBackend...")
    event = get_walter_backend_event(email)
    response = create_newsletter_and_send_entrypoint(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


if __name__ == "__main__":
    app()
